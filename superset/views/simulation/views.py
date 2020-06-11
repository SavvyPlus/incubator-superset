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
def handle_assumption_process(path, name, run_id, sim_num):
    g.user = None
    g.action_object = name
    g.action_object_type = 'Assumption'
    print('start preprocess')
    try:
        process_assumptions(path, run_id)
        assumption_file = db.session.query(Assumption).filter_by(name=name).one_or_none()
        assumption_file.status = "Processed"
        assumption_file.status_detail = None
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
    finally:
        simulation_start_invoker.apply_async(args=[run_id, sim_num])
        # simulation_start_invoker(run_id, sim_num)

def upload_assumption(path, name):
    download_link, s3_link = upload_assumption_file(path, name)
    assumption_file = db.session.query(Assumption).filter_by(name=name).one_or_none()
    if not assumption_file:
        assumption_file = Assumption()
    assumption_file.name = name
    assumption_file.status = "Uploaded"
    assumption_file.download_link = download_link
    assumption_file.s3_path = s3_link
    db.session.merge(assumption_file)
    db.session.commit()
    db.session.flush()
    return assumption_file.id, assumption_file.name


@celery_app.task
@simulation_logger.log_simulation(action_name='invoke')
def simulation_start_invoker(run_id, sim_num):
    from .invoker import batch_invoke_solver, batch_invoke_merger_all, batch_invoke_merger_year
    from .batch_parameters import generate_parameters_for_batch
    from .simulation_config import bucket_inputs
    print('start invoke')
    simulation = db.session.query(Simulation).filter_by(run_id=run_id).first()
    g.user = None
    g.action_object = simulation.name
    g.action_object_type = 'simulation'
    bucket_test = 'empower-simulation'

    # bucket_inputs = '007-spot-price-forecast-physical'
    # bucket_outputs = "dex-empower.test"

    # End early if assumption process failed
    if simulation.assumption.status != 'Processed':
        g.result = 'Run failed'
        g.detail = 'The assumption process failed, please check the detail of the assumption'
        pass
    else:

        generate_parameters_for_batch(run_id, sim_num)
        index_start = 0
        index_end = sim_num  # exclusive
        start_date = simulation.start_date
        end_date = simulation.end_date
        sim_tag = run_id
        total_days = (start_date - end_date).days
        output_days = total_days + 7 - total_days%7


        try:
            # TODO uncomment to invoke
            # batch_invoke_solver(bucket_test, sim_tag, index_start, index_end, interval=60)
            # batch_invoke_merger_year(bucket_test, sim_tag, index_start, index_end, output_days, year_start=simulation.start_date.year,
            #                          year_end=simulation.end_date.year, interval=30)
            # batch_invoke_merger_all(bucket_test, sim_tag, index_start, index_end, output_count=11, interval=60)
            batch_invoke_solver(bucket_inputs, 'Run_191', 0, 1, interval=500)
            # batch_invoke_merger_year(bucket_test, 'Run_191', 0, 1, output_days, year_start=simulation.start_date.year,
            #                          year_end=simulation.end_date.year, interval=500)
            # batch_invoke_merger_all(bucket_test, 'Run_191', 0, 1, output_count=1, interval=500)
            simulation.status = 'Run finished'
            db.session.commit()
            g.result = 'invoke success'
        except Exception as e:
            simulation.status = 'Run failed'
            simulation.status_detail = repr(e)
            db.session.commit()
            g.result = 'invoke failed'
            g.detail = repr(e)
            traceback.print_exc()


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
    list_columns = ['name', 'status', 'download_link']
    add_exclude_columns = ['status','status_detail', 's3_path']
    label_columns = {'name':'Name','status_detail':'Status Detail', 'download_link':'Download'}
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
            upload_assumption(path, name)
            # Do not do preprocess
            message = "Upload success"
            style = 'info'
            g.result = 'Upload success'
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
    add_columns = ['run_id','name', 'project', 'assumption','description', 'run_no', 'report_type', 'start_date', 'end_date']
    list_columns = ['name','assumption', 'project', 'status']
    edit_exclude_columns = ['status','status_detail']
    add_exclude_columns = ['status','status_detail', 'run_id']
    label_columns = {'run_no':'Number of simulation run'}

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
            item.status = 'Waiting for start'
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
            form.report_type.data = simulation.report_type
        return form

    @simulation_logger.log_simulation(action_name='upload assumption')
    @expose('/upload_assumption_ajax', methods=['POST'])
    def upload_assumption_ajax(self):
        file = request.files['file']
        file_name = request.form['name']
        run_id = request.form['run_id']
        g.action_object = file_name + '.xlsx'
        g.action_object_type = 'Assumption'
        try:

            path = os.path.join(app.config['UPLOAD_FOLDER'], file_name+'.xlsx')
            file.save(path)
            id, name = upload_assumption(path, file_name)
            message = 'Uploaded success. You can now choose the uploaded assumption in the list.'
            detail = {'name': name,
                      'id': id}
            g.result = 'Upload success'
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
        if not simulation:
            message = 'No simulation found for this run id, please refresh the page and try again.'
            g.result = 'Run failed'
            g.detail = message
        else:
            if simulation.assumption.status != 'Uploaded' and simulation.assumption.status != 'Processed':
                g.result = 'Run failed'
                message = 'The assumption is not uploaded successfully, please reupload or use another one.'
                g.detail = message
            else:
                if simulation.assumption.s3_path == None:
                    path = get_s3_url(bucket_test, excel_path.format(simulation.assumption.name))
                    simulation.assumption.s3_path = path
                    db.session.commit()
                try:
                    message = self.pre_run_check_process(simulation, run_type)

                except Exception as e:
                    g.result = 'Run failed'
                    g.detail =repr(e)
                    message = 'Run failed: ' + repr(e)

        return jsonify({
            'message': message,
        })

    def pre_run_check_process(self, simulation, run_type):
        pass_check, message = check_assumption(simulation.assumption.s3_path, simulation.assumption.name, simulation)
        if pass_check:
            g.result = 'Started, pre-process in progress'
            if run_type == 'test':
                sim_num = 10
                message = 'Test run started'
            else:
                sim_num = simulation.run_no
                message = 'Full run started'
            simulation.status = 'Running'
            db.session.commit()
            handle_assumption_process.apply_async(args=[simulation.assumption.s3_path, simulation.assumption.name,
                                                        simulation.run_id, sim_num])
            # handle_assumption_process(simulation.assumption.s3_path, simulation.assumption.name,
            #                                             simulation.run_id, sim_num)
        else:
            g.result = 'Run failed'
            g.detail = message
        return message


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


