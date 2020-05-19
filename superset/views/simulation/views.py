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
from flask import flash, redirect, g, request, abort
from flask_appbuilder.widgets import ListWidget
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

from .forms import UploadAssumptionForm
from .assumption_process import process_assumptions, upload_assumption_file
from .util import get_download_url

def upload_stream_write(form_file_field: "FileStorage", path: str):
    chunk_size = app.config["UPLOAD_CHUNK_SIZE"]
    with open(path, "bw") as file_description:
        while True:
            chunk = form_file_field.stream.read(chunk_size)
            if not chunk:
                break
            file_description.write(chunk)

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
        g.result = 'Success'
        g.detail = None
    except Exception as e:
        assumption_file = db.session.query(Assumption).filter_by(name=name).one_or_none()
        assumption_file.status = "Error"
        assumption_file.status_detail = repr(e)
        db.session.merge(assumption_file)
        db.session.commit()
        g.result = 'Failed'
        g.detail = repr(e)
        traceback.print_exc()

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
            message = "Upload success"
            style = 'info'
            g.result = 'Success'
            g.detail = None
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            message = "Upload failed:" + str(e)
            style = 'danger'
            g.result = 'Failed'
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
    def _add(self):
        is_valid_form = True
        get_filter_args(self._filters)
        exclude_cols = self._filters.get_relation_cols()
        form = self.add_form.refresh()
        if request.method == "POST":
            if form.validate():
                # Calling add simulation
                self.add_item(form, exclude_cols)
            else:
                is_valid_form = False
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
            flash(*self.datamodel.message)
        finally:
            return None


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

class ClientModelView(EmpowerModelView):

    class ClientListWidget(ListWidget):
        template = "empower/widgets/list_client.html"


    route_base = "/clientmodelview"
    datamodel = SQLAInterface(Client)
    include_route_methods = RouteMethod.CRUD_SET
    list_columns = ['name','description','projects']
    add_exclude_columns = ['projects']
    order_columns = ['name']

    list_widget = ClientListWidget

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
            project_dict[client.name] = list({'id': project.id, 'name': project.name} for project in projects)
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



class ProjectModelView(EmpowerModelView):
    route_base = "/projectmodelview"
    datamodel = SQLAInterface(Project)
    include_route_methods = RouteMethod.CRUD_SET

    add_exclude_columns = ['simulations']
    list_columns = ['name', 'description', 'client']
    order_columns = ['name','client']


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
            handle_assumption_process.apply_async(args=[s3_link, name])
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
            g.result = 'Success'
            g.detail = None
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            message = "Upload failed:" + str(e)
            style = 'danger'
            g.result = 'Failed'
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
    route_base = "/simulationmodelview"
    datamodel = SQLAInterface(Simulation)
    include_route_methods = RouteMethod.CRUD_SET

    list_columns = ['run_id', 'name','assumption', 'project', 'status']
    add_exclude_columns = ['status','status_detail']
    label_columns = {'run_no':'No. of simulation run'}

    @simulation_logger.log_simulation(action_name='create simulation')
    def add_item(self, form, exclude_cols):
        self._fill_form_exclude_cols(exclude_cols, form)

        item = self.datamodel.obj()
        try:
            form.populate_obj(item)

            g.action_object = item.name
            g.action_object_type = 'Simulation'
            g.result = 'Failed'
            g.detail = None
        except Exception as e:
            flash(str(e), "danger")
            g.detail = str(e)
        else:
            if self.datamodel.add(item):
                g.result = 'Success'
                g.detail = None

            flash(*self.datamodel.message)

    @simulation_logger.log_simulation(action_name='update simulation')
    def edit_item(self, form, item):
        g.action_object = item.name
        g.action_object_type = 'Simulation'
        g.result = 'Failed'
        g.detail = None
        try:
            form.populate_obj(item)
            self.pre_update(item)
        except Exception as e:
            g.detail = str(e)
            flash(str(e), "danger")
        else:
            if self.datamodel.edit(item):
                g.result = 'Success'
                g.detail = None
            flash(*self.datamodel.message)
        finally:
            return None


class SimulationLogModelView(SupersetModelView):
    route_base = "/simulationlog"
    datamodel = SQLAInterface(SimulationLog)
    include_route_methods = {RouteMethod.LIST, RouteMethod.SHOW, RouteMethod.INFO}

    list_columns = ['user', 'action', 'action_object', 'dttm', 'result']
    order_columns = ['user', 'action_object', 'action_object_type','dttm']

    base_order = ('dttm', 'desc')


