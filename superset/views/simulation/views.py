# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json
import traceback
import logging
import os
import tempfile
from flask import flash, redirect, g, request, abort, url_for, jsonify
from flask_appbuilder.widgets import ListWidget, FormWidget, ShowWidget
from flask_appbuilder import expose, has_access, SimpleFormView
from flask_appbuilder.urltools import get_filter_args, get_order_args, get_page_args, get_page_size_args
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_babel import lazy_gettext as _


from superset import app, db, event_logger, simulation_logger, celery_app
from superset.connectors.connector_registry import ConnectorRegistry
from superset.constants import RouteMethod
from superset.models.simulation import *
from superset.utils import core as utils
from superset.views.base import check_ownership, DeleteMixin, SupersetModelView

from .forms import UploadAssumptionForm, AddSimulationForm
from .assumption_process import process_assumptions, upload_assumption_file, check_assumption

def upload_stream_write(form_file_field: "FileStorage", path: str):
    chunk_size = app.config["UPLOAD_CHUNK_SIZE"]
    with open(path, "bw") as file_description:
        while True:
            chunk = form_file_field.stream.read(chunk_size)
            if not chunk:
                break
            file_description.write(chunk)

def send_notification(simulation, template_id):
    from superset.views.utils import send_sendgrid_mail
    email_list = [["Will", 'weiliang.zhou@zawee.work'],
                  ["Oscar", 'oscar.omegna@zawee.work'],
                  ["Dex", 'dexiao.ye@zawee.work']]
    message_dict = {"user": "{} {}".format(g.user.first_name, g.user.last_name),
                    "simulation": simulation.name,
                    "project": simulation.project.name,
                    "client": simulation.project.client.name,
                    }
    for email in email_list:
        message_dict['receiver'] = email[0]
        send_sendgrid_mail(email[1], message_dict, template_id)

@celery_app.task
@simulation_logger.log_simulation(action_name='process assumption')
def handle_assumption_process(path, name):
    g.user = None
    g.action_object = name
    g.action_object_type = 'Assumption'
    try:
        process_assumptions(path, name)
        assumption_file = db.session.query(Assumption).filter_by(name=name).one_or_none()
        assumption_file.status = "Success"
        assumption_file.status_detail = None
        # assumption_file.download_link = obj_url
        db.session.merge(assumption_file)
        db.session.commit()
        g.result = 'Process success'
        g.detail = 'The assumption detail is now on S3 empower-simulation bucket'
    except Exception as e:
        assumption_file = db.session.query(Assumption).filter_by(name=name).one_or_none()
        assumption_file.status = "Error"
        assumption_file.status_detail = repr(e)
        db.session.merge(assumption_file)
        db.session.commit()
        g.result = 'Process failed'
        g.detail = repr(e)
        traceback.print_exc()

def upload_assumption_and_trigger_process(path, name):
    download_link, s3_link = upload_assumption_file(path, name)
    handle_assumption_process.apply_async(args=[s3_link, name])
    assumption_file = db.session.query(Assumption).filter_by(name=name).one_or_none()
    if not assumption_file:
        assumption_file = Assumption()
    assumption_file.name = name
    assumption_file.status = "Processing"
    assumption_file.download_link = download_link
    db.session.merge(assumption_file)
    db.session.commit()
    db.session.flush()
    return assumption_file.id, assumption_file.name

class UploadAssumptionView(SimpleFormView):
    route_base = '/upload_assumption_file'
    form = UploadAssumptionForm
    form_template = "appbuilder/general/model/edit.html"
    form_title = "Upload assumption excel template"

    @simulation_logger.log_simulation(action_name='upload assumption')
    def form_post(self, form):
        import time
        time1 = time.time()
        excel_filename = form.excel_file.data.filename
        extension = os.path.splitext(excel_filename)[1].lower()
        path = tempfile.NamedTemporaryFile(
            dir=app.config["UPLOAD_FOLDER"], suffix=extension, delete=False
        ).name

        form.excel_file.data.filename = path
        name = form.name.data
        g.action_object = name
        g.action_object_type = 'Assumption'
        try:
            utils.ensure_path_exists(app.config["UPLOAD_FOLDER"])
            upload_stream_write(form.excel_file.data, path)
            upload_assumption_and_trigger_process(path, name)
            message = "Upload success"
            style = 'info'
            g.result = 'Upload success, processing'
            g.detail = None
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            message = "Upload failed:" + str(e)
            style = 'danger'
            g.result = 'Upload failed'
            g.detail = message
        finally:
            os.remove(path)
        # os.remove(path)
        flash(message, style)
        flash("Time used:{}".format(time.time() - time1), 'info')
        # message = 'Upload success'

        return redirect('/upload_assumption_file/form')


class AssumptionListWidget(ListWidget):
    template = 'empower/widgets/list_assumption.html'


class EmpowerModelView(SupersetModelView):
    """
    The base model view for empower, with modified workflow of crud.

    """
    """Customised show template, removed related views. Please create own show widget template 
    to display the related widget"""
    show_template = "empower/model/show.html"

    """Changed the value column to use list, avoid using generator in template render and"""
    def _get_list_widget(
        self,
        filters,
        actions=None,
        order_column="",
        order_direction="",
        page=None,
        page_size=None,
        widgets=None,
        **args,
    ):

        """ get joined base filter and current active filter for query """
        widgets = widgets or {}
        actions = actions or self.actions
        page_size = page_size or self.page_size
        if not order_column and self.base_order:
            order_column, order_direction = self.base_order
        joined_filters = filters.get_joined_filters(self._base_filters)
        count, lst = self.datamodel.query(
            joined_filters,
            order_column,
            order_direction,
            page=page,
            page_size=page_size,
        )
        pks = self.datamodel.get_keys(lst)

        # serialize composite pks
        pks = [self._serialize_pk_if_composite(pk) for pk in pks]

        widgets["list"] = self.list_widget(
            label_columns=self.label_columns,
            include_columns=self.list_columns,
            value_columns=list(self.datamodel.get_values(lst, self.list_columns)),
            order_columns=self.order_columns,
            formatters_columns=self.formatters_columns,
            page=page,
            page_size=page_size,
            count=count,
            pks=pks,
            actions=actions,
            filters=filters,
            modelview_name=self.__class__.__name__,
        )
        return widgets

    """Pass the related view widgets to show widget. Override the show widget to take the widget.get['related_views'] out"""
    def _get_show_widget(
        self, pk, item, widgets=None, actions=None, show_fieldsets=None
    ):
        widgets = widgets or {}
        actions = actions or self.actions
        show_fieldsets = show_fieldsets or self.show_fieldsets
        return self.show_widget(
            pk=pk,
            label_columns=self.label_columns,
            include_columns=self.show_columns,
            value_columns=list(self.datamodel.get_values_item(item, self.show_columns)),
            formatters_columns=self.formatters_columns,
            actions=actions,
            fieldsets=show_fieldsets,
            modelview_name=self.__class__.__name__,
            widgets=widgets,
        )

    """Override show logic, get related views first and used in show widget"""
    def _show(self, pk):
        """
            show function logic, override to implement different logic
            returns show and related list widget
        """
        pages = get_page_args()
        page_sizes = get_page_size_args()
        orders = get_order_args()

        item = self.datamodel.get(pk, self._base_filters)
        if not item:
            abort(404)

        self.update_redirect()
        widgets = self._get_related_views_widgets(
            item, orders=orders, pages=pages, page_sizes=page_sizes
        )
        widgets['show'] = self._get_show_widget(pk, item, widgets=widgets)
        return widgets

    """changed add workflow, separate post add, for logging"""
    def _add(self):
        is_valid_form = True
        get_filter_args(self._filters)
        exclude_cols = self._filters.get_relation_cols()
        form = self.add_form.refresh()
        if request.method == "POST":
            form = self.prefill_hidden_field(form)
            if form.validate():
                if self.add_item(form, exclude_cols):
                    return None
            else:
                is_valid_form = False
        else:
            form = self.prefill_form_add(form)
        if is_valid_form:
            self.update_redirect()
        return self._get_add_widget(form=form, exclude_cols=exclude_cols)

    def add_item(self, form, exclude_cols):
        self.process_form(form, True)
        item = self.datamodel.obj()

        try:
            form.populate_obj(item)
            self.pre_add(item)
        except Exception as e:
            flash(str(e), "danger")
        else:
            if self.datamodel.add(item):
                self.post_add(item)
                return True
            flash(*self.datamodel.message)
            return False

    def prefill_hidden_field(self, form):
        return form

    """Prefill the add form if adding to related view models. Override to get param from url and fill in form"""
    def prefill_form_add(self, form):
        return form

    """redirect to the show page, g.id is set in post add"""
    def post_add_redirect(self):
        return redirect(url_for('.show', pk=g.id))

    """set g.id for post add redirect"""
    def post_add(self, item):
        db.session.flush()
        g.id = item.id

    """changed the edit workflow, to separate post edit and able to log activity """
    def _edit(self, pk):
        """
            Edit function logic, override to implement different logic
            returns Edit widget and related list or None
        """
        is_valid_form = True
        pages = get_page_args()
        page_sizes = get_page_size_args()
        orders = get_order_args()
        get_filter_args(self._filters)
        exclude_cols = self._filters.get_relation_cols()

        item = self.datamodel.get(pk, self._base_filters)
        if not item:
            abort(404)
        # convert pk to correct type, if pk is non string type.
        pk = self.datamodel.get_pk_value(item)

        if request.method == "POST":
            form = self.edit_form.refresh(request.form)
            # fill the form with the suppressed cols, generated from exclude_cols
            self._fill_form_exclude_cols(exclude_cols, form)
            # trick to pass unique validation
            form._id = pk
            if form.validate():
                self.edit_item(form, item)
            else:
                is_valid_form = False
        else:
            # Only force form refresh for select cascade events
            form = self.edit_form.refresh(obj=item)
            # Perform additional actions to pre-fill the edit form.
            self.prefill_form(form, pk)

        widgets = self._get_edit_widget(form=form, exclude_cols=exclude_cols)
        widgets = self._get_related_views_widgets(
            item,
            filters={},
            orders=orders,
            pages=pages,
            page_sizes=page_sizes,
            widgets=widgets,
        )
        if is_valid_form:
            self.update_redirect()
        return widgets

    def edit_item(self, form, item):
        self.process_form(form, False)

        try:
            form.populate_obj(item)
            self.pre_update(item)
        except Exception as e:
            flash(str(e), "danger")
        else:
            if self.datamodel.edit(item):
                self.post_update(item)
            flash(*self.datamodel.message)
        finally:
            return None


class AssumptionModelView(EmpowerModelView):
    route_base = "/assuptionmodelview"
    datamodel = SQLAInterface(Assumption)
    include_route_methods = RouteMethod.CRUD_SET
    list_widget = AssumptionListWidget

    order_columns = ['name']
    list_columns = ['name', 'status', 'status_detail', 'download_link']
    add_exclude_columns = ['status','status_detail']
    label_columns = {'name':'Name','status':'Status','status_detail':'Status Detail', 'download_link':'Download'}
    edit_exclude_columns = ['status','status_detail','download_link']
    show_exclude_columns = ['download_link']


    add_form = UploadAssumptionForm

    @simulation_logger.log_simulation(action_name='upload assumption')
    def add_item(self, form, exclude_cols):
        import time
        time1 = time.time()
        excel_filename = form.download_link.data.filename
        extension = os.path.splitext(excel_filename)[1].lower()
        path = tempfile.NamedTemporaryFile(
            dir=app.config["UPLOAD_FOLDER"], suffix=extension, delete=False
        ).name

        form.download_link.data.filename = path
        name = form.name.data
        g.action_object = name
        g.action_object_type = 'Assumption'
        try:
            utils.ensure_path_exists(app.config["UPLOAD_FOLDER"])
            upload_stream_write(form.download_link.data, path)
            download_link, s3_link = upload_assumption_file(path, name)
            msg = check_assumption(path, name)
            if msg != 'success':
                raise Exception(msg)
            # handle_assumption_process.apply_async(args=[s3_link, name])
            assumption_file = db.session.query(Assumption).filter_by(name=name).one_or_none()
            if not assumption_file:
                assumption_file = Assumption()
            assumption_file.name = name
            assumption_file.status = "Processing"
            assumption_file.download_link = download_link
            db.session.merge(assumption_file)
            db.session.commit()
            message = "Upload success"
            style = 'info'
            g.result = 'Upload success, processing'
            g.detail = None
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            message = "Upload failed:" + str(e)
            style = 'danger'
            g.result = 'Upload failed'
            g.detail = message
        finally:
            os.remove(path)
        # os.remove(path)
        flash(message, style)
        flash("Time used:{}".format(time.time() - time1), 'info')
        return None


class SimulationModelView(
    EmpowerModelView
):

    class SimulationAddWidget(FormWidget):
        template = 'empower/widgets/add_simulation.html'

    class SimulationListWidget(ListWidget):
        template = 'empower/widgets/list_simulation.html'

    route_base = "/simulationmodelview"
    datamodel = SQLAInterface(Simulation)
    include_route_methods = RouteMethod.CRUD_SET | {
        'upload_assumption_ajax',
        'start_run',
    }

    list_columns = ['run_id', 'name','assumption', 'project', 'status']
    # add_columns = ['name','run_id','description','assumption_choice1','assumption_choice2','generation_model',
    #                'run_no','start_date','end_date','report_type']
    edit_exclude_columns = ['status','status_detail']
    edit_columns = ['name','run_id','project','assumption','run_no','report_type','start_date','end_date']
    add_exclude_columns = ['status','status_detail']
    label_columns = {'run_no':'No. of simulation run'}

    add_widget = SimulationAddWidget
    # add_form = AddSimulationForm
    list_widget = SimulationListWidget

    def _get_list_widget(
            self,
            filters,
            actions=None,
            order_column="",
            order_direction="",
            page=None,
            page_size=None,
            widgets=None,
            **args,
    ):

        """ get joined base filter and current active filter for query """
        widgets = widgets or {}
        actions = actions or self.actions
        page_size = page_size or self.page_size
        if not order_column and self.base_order:
            order_column, order_direction = self.base_order
        joined_filters = filters.get_joined_filters(self._base_filters)
        count, lst = self.datamodel.query(
            joined_filters,
            order_column,
            order_direction,
            page=page,
            page_size=page_size,
        )
        pks = self.datamodel.get_keys(lst)
        base_url = url_for('SimulationModelView.add')
        projects = db.session.query(Project).all()
        if len(joined_filters.filters) > 0:
            for filter, value in zip(joined_filters.filters, joined_filters.values):
                if filter.column_name == 'project':
                    project = db.session.query(Project).filter_by(id=value).first()
                    client = project.client
                    projects = client.projects
        # serialize composite pks
        pks = [self._serialize_pk_if_composite(pk) for pk in pks]

        widgets["list"] = self.list_widget(
            label_columns=self.label_columns,
            include_columns=self.list_columns,
            value_columns=self.datamodel.get_values(lst, self.list_columns),
            order_columns=self.order_columns,
            formatters_columns=self.formatters_columns,
            page=page,
            page_size=page_size,
            count=count,
            pks=pks,
            actions=actions,
            filters=filters,
            modelview_name=self.__class__.__name__,
            projects=projects,
            url=base_url,
        )
        return widgets

    @simulation_logger.log_simulation(action_name='create simulation')
    def add_item(self, form, exclude_cols):
        self._fill_form_exclude_cols(exclude_cols, form)

        item = self.datamodel.obj()
        try:
            form.populate_obj(item)

            g.action_object = item.name
            g.action_object_type = 'Simulation'
            g.result = 'Create simulation failed'
            g.detail = None
        except Exception as e:
            flash(str(e), "danger")
            g.detail = str(e)
        else:
            if self.datamodel.add(item):
                self.post_add(item)
                g.result = 'Create simulation success'
                g.detail = None
                self.post_add(item)
                # send_notification(item, 'd-a55f374a820b4aa08ebc6eb132504151')
                return True
            flash(*self.datamodel.message)
            return False

    @simulation_logger.log_simulation(action_name='update simulation')
    def edit_item(self, form, item):
        g.action_object = item.name
        g.action_object_type = 'Simulation'
        g.result = 'Update simulation failed'
        g.detail = None
        try:
            form.populate_obj(item)
            self.pre_update(item)
        except Exception as e:
            g.detail = str(e)
            flash(str(e), "danger")
        else:
            if self.datamodel.edit(item):
                g.result = 'Update simulation success'
                g.detail = None
                # send_notification(item, '123')
            flash(*self.datamodel.message)
        finally:
            return None

    def prefill_form_add(self, form):
        flt_dic = self.get_filter_args()
        if 'project' in flt_dic.keys():
            project = db.session.query(Project).filter_by(id=flt_dic['project']).one_or_none()
            form.report_type.data = project.job_types
        if 'sim' in flt_dic.keys():
            simulation = db.session.query(Simulation).filter_by(id=flt_dic['sim']).first()
            form.assumption.data = simulation.assumption
            form.description.data = 'Re run for simulation' + simulation.name
            form.name.data = simulation.name + '_re_run'
            form.report_type.data = simulation.report_type
            form.start_date.data = simulation.start_date
            form.end_date.data = simulation.end_date
            form.run_no.data = simulation.run_no
            form.run_id.data = simulation.run_id
            form.report_type.data = simulation.report_type
        return form

    @simulation_logger.log_simulation(action_name='upload assumption')
    @expose('/upload_assumption_ajax', methods=['POST'])
    def upload_assumption_ajax(self):
        file = request.files['file']
        try:
            g.action_object = file.filename + '.xlsx'
            g.action_object_type = 'Assumption'
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            file_name = file.filename.split('.')[0]
            id, name = upload_assumption_and_trigger_process(path, file_name)
            message = 'Uploaded success. You can now choose the uploaded assumption in the list. The assumption ' + \
                      'processing is running on backend and will be ready soon.'
            detail = {'name': name,
                      'id': id}
            g.result = 'Upload success, processing'
            g.detail = None
        except Exception as e:
            message = 'Failed. {}'.format(repr(e))
            detail = repr(e)
            g.result = 'Upload failed'
            g.detail = detail
        finally:
            # os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            return jsonify({
                'message': message,
                'detail': detail
            })

    def prefill_hidden_field(self, form):
        flt_dic = self.get_filter_args()
        # print(form)
        if 'project' in flt_dic.keys():
            project = db.session.query(Project).filter_by(id=flt_dic['project']).one_or_none()
            form.project.data = project
        return form

    def get_filter_args(self):
        import re
        result = {}
        for arg in request.args:
            proj_match = re.findall("_flt_0_project", arg)
            sim_match = re.findall("simID", arg)
            if proj_match:
                result['project'] = request.args.get(arg)
            if sim_match:
                result['sim'] = request.args.get(arg)
        return result

    @simulation_logger.log_simulation(action_name='start run')
    @expose('/start_run/<id>/<run_type>/')
    def start_run(self,id,run_type):
        from superset.views.simulation.util import get_s3_url
        from superset.views.simulation.helper import excel_path, bucket_test
        simulation = db.session.query(Simulation).filter_by(id=id).one_or_none()
        message = None
        if not simulation:
            message = 'No simulation found for this run id, please refresh the page and try again.'
            g.result = 'Run failed'
            g.detail = message
        else:
            if simulation.assumption.status != 'Success':

                g.result = 'Run failed'
                if simulation.assumption.status == 'Processing':
                    message = 'The assumption file of this simulation is in processing, please start run after finished.'
                elif simulation.assumption.status == 'Error':
                    message = 'There is error during the processing of the assumption file, please choose another assumption.'
                g.detail = message
                pass
            assumption_path = get_s3_url(bucket_test, excel_path.format(simulation.assumption.name))
            try:
                msg = check_assumption(assumption_path, simulation.assumption.name)
                if msg == 'success':
                    if run_type == 'test':
                        message = 'Test run started'
                    else:
                        message = 'Full run started'
                else:
                    pass
            except Exception as e:
                message = repr(e)
        return jsonify({
            'message': message,
        })




class ProjectModelView(EmpowerModelView):

    class ProjectShowWidget(ShowWidget):
        template = "empower/widgets/show_project.html"

    route_base = "/projectmodelview"
    datamodel = SQLAInterface(Project)
    include_route_methods = RouteMethod.CRUD_SET

    add_exclude_columns = ['simulations']
    edit_exclude_columns = ['simulations']
    list_columns = ['name', 'description', 'client']
    order_columns = ['name']

    show_widget = ProjectShowWidget

    related_views = [SimulationModelView]

    @simulation_logger.log_simulation(action_name='update project')
    def edit_item(self, form, item):
        g.action_object = item.name
        g.action_object_type = 'Project'
        g.result = 'Update project failed'
        g.detail = None
        try:
            form.populate_obj(item)
            self.pre_update(item)
        except Exception as e:
            g.detail = str(e)
            flash(str(e), "danger")
        else:
            if self.datamodel.edit(item):
                g.result = 'Update project success'
                g.detail = None
                # send_notification(item, '123')
            flash(*self.datamodel.message)
        finally:
            return None

    def prefill_hidden_field(self, form):
        flt_dic = self.get_filter_args()
        # print(form)
        if 'client' in flt_dic.keys():
            client = db.session.query(Client).filter_by(id=flt_dic['client']).one_or_none()
            form.client.data = client
        return form

    def get_filter_args(self):
        import re
        result = {}
        for arg in request.args:
            re_match = re.findall("_flt_0_client", arg)
            if re_match:
                result['client'] = request.args.get(re_match[0])
        return result

    def pre_delete(self, item):
        if item.simulations is not None:
            raise Exception('This project has modeling jobs associate with it. Please delete the models first.')


class ClientModelView(EmpowerModelView):

    class ClientListWidget(ListWidget):
        template = "empower/widgets/list_client.html"

    class ClientShowWidget(ShowWidget):
        template = "empower/widgets/show_client.html"

    route_base = "/clientmodelview"
    datamodel = SQLAInterface(Client)
    include_route_methods = RouteMethod.CRUD_SET
    list_columns = ['name','description']
    add_exclude_columns = ['projects']
    edit_exclude_columns = ['projects']
    order_columns = ['name']

    related_views = [ProjectModelView]

    list_widget = ClientListWidget
    show_widget = ClientShowWidget

    def _get_list_widget(
        self,
        filters,
        actions=None,
        order_column="",
        order_direction="",
        page=None,
        page_size=None,
        widgets=None,
        **args,
    ):
        """ get joined base filter and current active filter for query """
        widgets = widgets or {}
        actions = actions or self.actions
        page_size = page_size or self.page_size
        if not order_column and self.base_order:
            order_column, order_direction = self.base_order
        joined_filters = filters.get_joined_filters(self._base_filters)
        count, lst = self.datamodel.query(
            joined_filters,
            order_column,
            order_direction,
            page=page,
            page_size=page_size,
        )
        pks = self.datamodel.get_keys(lst)

        # dict of clients and projects, each client has a list of projects where each project is a dict of id and name
        # can be used to create link for edit project later
        project_dict = {}
        for client in lst:
            projects = client.projects
            project_dict[client.name] = list({'id':project.id, 'name': project.name} for project in projects)
        # serialize composite pks
        pks = [self._serialize_pk_if_composite(pk) for pk in pks]

        widgets["list"] = self.list_widget(
            label_columns=self.label_columns,
            include_columns=self.list_columns,
            value_columns=self.datamodel.get_values(lst, self.list_columns),
            order_columns=self.order_columns,
            formatters_columns=self.formatters_columns,
            page=page,
            project_dict=project_dict,
            page_size=page_size,
            count=count,
            pks=pks,
            actions=actions,
            filters=filters,
            modelview_name=self.__class__.__name__,
        )
        return widgets

    def pre_delete(self, item):
        if item.projects is not None:
            raise Exception("This client has projects associate with it. Please delete the projects first.")


class SimulationLogModelView(SupersetModelView):
    route_base = "/simulationlog"
    datamodel = SQLAInterface(SimulationLog)
    include_route_methods = {RouteMethod.LIST, RouteMethod.SHOW, RouteMethod.INFO}

    list_columns = ['user', 'action', 'action_object', 'dttm', 'result']
    order_columns = ['user', 'action_object', 'action_object_type','dttm']

    base_order = ('dttm', 'desc')
    page_size = 20


