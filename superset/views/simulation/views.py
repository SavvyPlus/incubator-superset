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

import ast
import json
import traceback
import logging
import os
import tempfile
import pytz
import superset.models.core as models
from flask import flash, redirect, g, request, abort, url_for, jsonify
from flask_appbuilder.widgets import ListWidget, FormWidget, ShowWidget
from flask_appbuilder import expose, has_access, SimpleFormView
from flask_appbuilder.actions import action
from flask_appbuilder.urltools import get_filter_args, get_order_args, get_page_args, get_page_size_args
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_babel import lazy_gettext as _

from superset import app, db, event_logger, simulation_logger, celery_app
from superset.typing import FlaskResponse
from superset.constants import RouteMethod
from superset.models.simulation import *
from superset.models.assumption_check import *
from superset.models.slice import Slice
from flask_appbuilder.security.sqla import models as ab_models
from superset.connectors.sqla.models import SqlaTable
from superset.utils import core as utils
from superset.sql_parse import Table
from superset.views.base import json_success, json_error_response, DeleteMixin, SupersetModelView, common_bootstrap_payload
from superset.views.utils import send_sendgrid_mail
from superset.views.simulation.util import get_s3_url
from superset.views.simulation.simulation_config import excel_path, bucket_inputs, bucket_hist

from .forms import UploadAssumptionForm, SimulationForm, UploadAssumptionFormForStanding
from .util import send_sqs_msg, get_current_external_ip
from .assumption_process import process_assumptions, upload_assumption_file, check_assumption, process_assumption_to_df_dict,\
    save_as_new_tab_version, ref_day_generation_check, check_assumption_processed
from .util import get_redirect_endpoint, read_excel, download_from_s3, get_full_week_end_date, from_dict, upload_stream_write,\
    read_file_byte_from_s3
from ..utils import bootstrap_user_data, create_attachment


# def upload_stream_write(form_file_field: "FileStorage", path: str):
#     chunk_size = app.config["UPLOAD_CHUNK_SIZE"]
#     with open(path, "bw") as file_description:
#         while True:
#             chunk = form_file_field.stream.read(chunk_size)
#             if not chunk:
#                 break
#             file_description.write(chunk)


def send_notification(simulation, template_id):

    email_list = [["Colin", 'chenyang.wang@zawee.work']]
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
        assumption_file = find_assumption_by_name(db.session, name)
        assumption_file.status = "Processed"
        assumption_file.status_detail = None
        db.session.merge(assumption_file)
        db.session.commit()
        g.result = 'Process success'
        g.detail = 'The assumption detail is now on S3 {} bucket.'.format(bucket_inputs)
    except Exception as e:
        assumption_file = find_assumption_by_name(db.session, name)
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
    assumption_file = find_assumption_by_name(db.session, name)
    if not assumption_file:
        assumption_file = Assumption()
        assumption_file.name = name
        db.session.add(assumption_file)
        db.session.flush()
    assumption_file.status = "Uploaded"
    assumption_file.download_link = download_link
    assumption_file.s3_path = s3_link
    db.session.merge(assumption_file)
    db.session.commit()
    refresh_time = 0
    while assumption_file.id == None and refresh_time <3:
        import time
        refresh_time = refresh_time+1
        db.session.flush()
        time.sleep(0.3)
    return assumption_file.id, assumption_file.name


@celery_app.task
@simulation_logger.log_simulation(action_name='invoke')
def simulation_start_invoker(run_id, sim_num, start_run_msg=None):
    from .invoker import batch_invoke_solver, batch_invoke_merger_all, batch_invoke_merger_year, invoker
    from .batch_parameters import generate_parameters_for_batch
    from .simulation_config import bucket_inputs
    print('start invoke')
    simulation = db.session.query(Simulation).filter_by(run_id=run_id).first()
    print('found simulation {}'.format(simulation.name))
    g.user = None
    g.action_object = simulation.name
    g.action_object_type = 'simulation'

    if sim_num < 2:
        interval=300
    elif sim_num < 6:
        interval = 100
    else:
        interval = 60

    # End early if assumption process failed
    if simulation.assumption.status != 'Processed':
        g.result = 'Run failed'
        g.detail = 'The assumption process failed, please check the detail of the assumption'
        simulation.status = 'Run failed'
        simulation.status_detail = 'The assumption process failed, please check the detail of the assumption'
        db.session.commit()
    else:
        try:
            print('generate parameters')
            generate_parameters_for_batch(simulation, sim_num)
            print('invoking')
            index_start = 0
            index_end = sim_num  # exclusive
            # start_date = simulation.start_date
            start_date = simulation.start_date
            # end_date = simulation.end_date
            end_date = get_full_week_end_date(start_date, simulation.end_date)
            total_days = (end_date - start_date).days + 1
            sim_tag = run_id
            if not start_run_msg:
                # Find duids from last start run log
                latest_sim = db.session.query(SimulationLog).filter_by(
                    action_object_type='Simulation',
                    action_object=simulation.name,
                    action='start run',
                    result='Started, pre-process in progress'
                ).order_by(SimulationLog.dttm.desc()).first()
                start_run_msg = ast.literal_eval(latest_sim.detail)

            template = json.loads(read_file_byte_from_s3(bucket_inputs, glue_crawler_template_path))

            print('Start run info: ' + repr(start_run_msg))
            template['run_id'] = run_id
            template['num_sim'] = str(sim_num)
            template['outSimBucket'] = bucket_inputs
            template['outExcelBucket'] = bucket_inputs
            template['duids'] = start_run_msg['duids']
            template['start_date'] = start_run_msg['simStartDate']
            template['end_date'] = start_run_msg['simEndDate']
            template['supersetURL'] = start_run_msg['supersetURL']
            template['email'] = start_run_msg['email']
            print('Glue template: ' + repr(template))
            if not send_sqs_msg(json.dumps(template), queue_url=glue_trigger_sqs_url):
                raise Exception('Failed to send glue crawler sqs message. Please contact dev team.')
            batch_invoke_solver(bucket_inputs, sim_tag, index_start, index_end, interval=interval)
            batch_invoke_merger_year(bucket_inputs, sim_tag, index_start, index_end, total_days, year_start=start_date.year,
                                     year_end=end_date.year+1, interval=interval/2)
            batch_invoke_merger_all(bucket_inputs, sim_tag, index_start, index_end, end_date.year-start_date.year,
                                    interval=interval/2)
            # batch_invoke_solver(bucket_inputs, 'Run_191', 0, 1, interval=500)
            # batch_invoke_merger_year(bucket_test, 'Run_191', 0, 1, output_days, year_start=simulation.start_date.year,
            #                          year_end=simulation.end_date.year, interval=500)
            # batch_invoke_merger_all(bucket_test, 'Run_191', 0, 1, output_count=1, interval=500)
            invoker(payload={'run_id': sim_tag, 'bucket': bucket_inputs, 'supersetURL': get_current_external_ip()},
                    function_name='spot-simulation-prod-stk-check-spot-output')

            # simulation.status = 'Run finished'
            #
            # db.session.commit()
            g.result = 'Invoke success, simulation finished.'
            # message = 'Simulation {} is finished successfully, an email contain links to the result will be sent to you shortly.'
            # style='info'
        except Exception as e:
            simulation.status = 'Run failed'
            simulation.status_detail = repr(e)
            db.session.commit()
            g.result = 'Invoke failed'
            g.detail = repr(e)
            traceback.print_exc()
            # message = 'Simulation {} has failed, please check log for the detail.'
            # style = 'danger'
        finally:
            print('invoke finished')
            # flash(message, style)


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

    """Pass the related view widgets to show widget. Override the show widget to take the
     widget.get['related_views'] out"""
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

    """Prefill the add form if adding to related view models. Override to get param from
    url and fill in form"""
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
    edit_exclude_columns = ['status','status_detail','download_link', 's3_path']
    show_exclude_columns = ['download_link', 's3_path']

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


class EditAssumptionModelView(
    SupersetModelView, DeleteMixin
):  # pylint: disable=too-many-ancestors
    route_base = "/edit-assumption"
    default_view = 'assumption'
    datamodel = SQLAInterface(Slice)

    @expose("/assumption/")
    def assumption(self):
        username = g.user.username

        user = (
            db.session.query(ab_models.User).filter_by(username=username).one_or_none()
        )
        if not user:
            abort(404, description=f"User: {username} does not exist.")

        payload = {
            "user": bootstrap_user_data(user, include_perms=True),
            "common": common_bootstrap_payload(),
        }

        return self.render_template(
            "superset/basic.html",
            title=_("Edit Assumption"),
            entry="assumption",
            bootstrap_data=json.dumps(
                payload, default=utils.pessimistic_json_iso_dttm_ser
            ),
        )

    @expose('/upload-file/', methods=['POST'])
    def upload_file(self):
        form = request.form
        table = form['table']
        note = form['note']
        file = request.files.get('file')
        scenario = None
        if 'scenario' in form.keys():
            scenario = form['Scenario']
        file_name = file.filename
        extension = os.path.splitext(file_name)[1].lower()
        path = tempfile.NamedTemporaryFile(
            dir=app.config["UPLOAD_FOLDER"], suffix=extension, delete=False
        ).name
        try:
            utils.ensure_path_exists(app.config["UPLOAD_FOLDER"])
            upload_stream_write(file, path)
            tab_model = find_table_class_by_name(table)
            tab_def_model = find_table_class_by_name(table+'Definition')
            if extension in ['.xlsx', '.xls']:
                df = read_excel(path)
            else:
                raise Exception('Please choose excel file with xlsx or xls format.')
            new_def = save_as_new_tab_version(db, df, tab_def_model, tab_model, note=note, scenario=scenario)
            message = 'Update table successful'
        except Exception as e:
            db.session.rollback()
            traceback.print_exc()
            message = repr(e)
        finally:
            os.remove(path)

        return jsonify({
            'message': message
        })

    @expose("/get-data/<table>/<request_type>/<ver>/")
    def get_data(self, table: str, request_type: str, ver: str):
        # form = request.form
        # table = form['table']
        tab_def_model = find_table_class_by_name(table + 'Definition')
        if request_type == 'version':
            version_list = db.session.query(tab_def_model).all()
            versions = []
            if len(version_list)>0:
                for version in version_list:
                    versions.append({
                        'version': version.get_version(),
                        'note': version.get_note(),
                    })

            message = {
                'versions': versions
            }
        else:
            tab_data_model = find_table_class_by_name(table)
            version = ver
            tab_data = db.session.query(tab_data_model).filter_by(Version=version).all()
            headers = tab_data_model().get_header_and_type()
            data_list = []
            for row_data in tab_data:
                data_list.append(row_data.get_dict())
            message = {
                'header': headers,
                'data': data_list
            }
        return jsonify(message)

    @expose("/save-data/", methods=['POST'])
    def save_data(self):
        try:
            form = request.form
            table = json.loads(form.get('table'))
            data_list = json.loads(form.get('data'))['data']
            if 'tableData' in data_list[0].keys():
                for data in data_list:
                    del data['tableData']
            note = json.loads(form.get('note'))
            tab_data_model = find_table_class_by_name(table)
            tab_def_model = find_table_class_by_name(table+'Definition')
            print(data_list)
            df = from_dict(data_list)
            new_def = save_as_new_tab_version(db, df, tab_def_model, tab_data_model, note=note)
            message = {'message': 'Data has been saved as new version'}
        except Exception as e:
            db.session.rollback()
            traceback.print_exc()
            message = {'message': repr(e)}

        return jsonify(message)


class UploadExcelView(SimpleFormView):
    route_base = '/upload_base_excel'
    form_title = 'Upload assumption excel'
    form = UploadAssumptionFormForStanding
    form_template = "appbuilder/general/model/edit.html"

    def form_post(self, form):
        file_name = form.file.data.filename
        extension = os.path.splitext(file_name)[1].lower()
        path = tempfile.NamedTemporaryFile(
            dir=app.config["UPLOAD_FOLDER"], suffix=extension, delete=False
        ).name

        form.file.data.filename = path
        name = form.name.data
        g.action_object = name
        g.action_object_type = 'Assumption'
        try:
            utils.ensure_path_exists(app.config["UPLOAD_FOLDER"])
            upload_stream_write(form.file.data, path)
            df_dict = process_assumption_to_df_dict(path)
            new_assum_def = AssumptionDefinition()
            new_assum_def.Name = name
            for tab_def_model, tab_data_model in model_list:
                tab_def_model = find_table_class_by_name(tab_def_model)
                tab_data_model = find_table_class_by_name(tab_data_model)
                sheet_name = tab_def_model.get_sheet_name()
                sub_tab_def = save_as_new_tab_version(db, df_dict[sheet_name],
                                                      tab_def_model, tab_data_model,
                                                      note=name)
                # set relation of assumption def with sub table definition
                new_assum_def.__setattr__(tab_def_model.__tablename__, sub_tab_def)
            db.session.add(new_assum_def)
            db.session.commit()
            message = 'success'
            style = 'info'
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            message = repr(e)
            style = 'danger'
        finally:
            os.remove(path)
        flash(message, style)
        return redirect(self.route_base + '/form')

class SimulationModelView(
    EmpowerModelView
):

    class SimulationAddWidget(FormWidget):
        template = 'empower/widgets/add_simulation.html'

    class SimulationListWidget(ListWidget):
        template = 'empower/widgets/list_simulation.html'

    class SimulationShowWidget(ShowWidget):
        template = 'empower/widgets/show_simulation.html'

    route_base = "/simulationmodelview"
    datamodel = SQLAInterface(Simulation)
    include_route_methods = RouteMethod.CRUD_SET | {
        'upload_assumption_ajax',
        'load_results',
        'send_email',
        'process_success',
        'process_failed',
        'start_run',
        'query_success',
        'query_failed',
        'query_result',
    }
    add_columns = ['name', 'project', 'assumption','description', 'run_no', 'report_type', 'start_date', 'end_date']
    list_columns = ['name','assumption', 'project', 'run_dttm', 'status']
    edit_exclude_columns = ['status_detail', 'run_id', 'chart_links']
    # label_columns = {'run_no':'Number of simulation run'}

    add_widget = SimulationAddWidget
    add_form = SimulationForm
    list_widget = SimulationListWidget
    show_widget = SimulationShowWidget
    # edit_form = SimulationForm

    @event_logger.log_this
    @expose('/load-results/<run_id>/<table_name>/')
    def load_results(self, run_id: str, table_name: str) -> FlaskResponse:
        # First， check if the table has existed. If so, redirect to its chart
        sqla_table = db.session.query(SqlaTable).filter_by(table_name=table_name).one_or_none()
        if sqla_table:
            endpoint = get_redirect_endpoint(table_name, sqla_table.id)
            return redirect(endpoint)

        # If this is a new table, load it into Superset and redirect to its chart
        csv_table = Table(table=table_name, schema=None)
        s3_file_path = 's3://{}/result-spot-price-forecast-simulation-statistics/{}/{}.csv'.format(bucket_inputs, run_id, table_name)

        try:
            database = (
                db.session.query(models.Database).filter_by(id=1).one()
            )
            csv_to_df_kwargs = {
                "sep": ',',
                "header": 0,
                "index_col": None,
                "mangle_dupe_cols": True,
                "skipinitialspace": False,
                "skiprows": None,
                "nrows": None,
                "skip_blank_lines": True,
                "parse_dates": None,
                "infer_datetime_format": True,
                "chunksize": 1000,
            }
            df_to_sql_kwargs = {
                "name": csv_table.table,
                "if_exists": 'fail',
                "index": False,
                "index_label": None,
                "chunksize": 1000,
            }
            database.db_engine_spec.create_table_from_csv(
                s3_file_path,
                csv_table,
                database,
                csv_to_df_kwargs,
                df_to_sql_kwargs,
            )

            # Connect table to the database that should be used for exploration.
            # E.g. if hive was used to upload a csv, presto will be a better option
            # to explore the table.
            expore_database = database
            explore_database_id = database.get_extra().get("explore_database_id", None)
            if explore_database_id:
                expore_database = (
                    db.session.query(models.Database)
                    .filter_by(id=explore_database_id)
                    .one_or_none()
                    or database
                )

            sqla_table = (
                db.session.query(SqlaTable)
                .filter_by(
                    table_name=csv_table.table,
                    schema=csv_table.schema,
                    database_id=expore_database.id,
                )
                .one_or_none()
            )

            if sqla_table:
                sqla_table.fetch_metadata()
            if not sqla_table:
                sqla_table = SqlaTable(table_name=csv_table.table)
                sqla_table.database = expore_database
                sqla_table.database_id = database.id
                sqla_table.user_id = g.user.id
                sqla_table.schema = csv_table.schema
                sqla_table.fetch_metadata()
                db.session.add(sqla_table)
            db.session.commit()

            added_sqla_table = (
                db.session.query(SqlaTable).filter_by(table_name=csv_table.table).one()
            )
        except ValueError as ve:
            db.session.rollback()
            flash(str(ve), "danger")

            return redirect("/simulationmodelview/list/")
        except Exception as ex:  # pylint: disable=broad-except
            db.session.rollback()

            message = _(
                'Unable to load CSV file to table '
            )

            flash(message, "danger")
            return redirect("/simulationmodelview/list/")

        message = _(
            'CSV file "%(csv_filename)s" uploaded to table "%(table_name)s" in '
            'database "%(db_name)s"',
            csv_filename=s3_file_path.split('/')[-1],
            table_name=str(csv_table),
            db_name=database.database_name,
        )
        flash(message, "info")

        endpoint = get_redirect_endpoint(table_name, added_sqla_table.id)
        return redirect(endpoint)

    @event_logger.log_this
    @expose('/send-email/<run_id>/<sim_num>/')
    def send_email(self, run_id: str, sim_num: str) -> FlaskResponse:
        # Get user email
        simulation = db.session.query(Simulation).filter_by(run_id=run_id).first()
        if not simulation:
            return json_error_response("Simulation " + run_id + " does not exist in db")
        else:
            latest_sim = db.session.query(SimulationLog).filter_by(
                action_object_type='Simulation',
                action_object=simulation.name,
                action='start run',
                # result='Started, pre-process in progress'
            ).order_by(SimulationLog.dttm.desc()).first()
            if not latest_sim:
                return json_error_response("Simulation " + run_id + " has not started yet")
            else:
                email_to = latest_sim.user.email
                assumption_name = simulation.assumption.name
                project_name = simulation.project.name
                simulation_name = simulation.name
                simulation_description = simulation.description or ''
                simulation_id = str(simulation.id)

        # Send notification email
        # base_url = "http://localhost:9000/simulationmodelview/"
        # base_url = f"{get_current_external_ip()}/simulationmodelview/"
        base_url = "https://app.empoweranalytics.com.au/simulationmodelview/"
        forecast_url = base_url + "load-results/" + run_id + "/spot_price_percentiles_" + run_id + "_" + sim_num + "sims/"
        cap_url = base_url + "load-results/" + run_id + "/300_Cap_Payouts_percentiles_" + run_id + "_" + sim_num + "sims/"
        distribution_url = base_url + "load-results/" + run_id + "/spot_price_distribution_" + run_id + "_" + sim_num + "sims/"
        dynamic_template_data = {
            "run_id": run_id,
            "assumption_name": assumption_name,
            "project_name": project_name,
            "simulation_name": simulation_name,
            "simulation_description": simulation_description,
            "simulation_url": base_url + "show/" + simulation_id,
            "spot_price_forecast": forecast_url,
            "cap_of_300": cap_url,
            "spot_price_distribution": distribution_url,
        }
        send_sendgrid_mail(email_to, dynamic_template_data, 'd-622c2bd9a8eb49a2bbfa98a0a93ce65f')

        # Change simulation status to finished when sending result emial
        simulation.status = 'Run finished'
        simulation.status_detail = None
        # record run finish datetime
        aest = pytz.timezone('Australia/Melbourne')
        simulation.run_dttm = datetime.datetime.now(aest)
        chart_link1 = ChartLink('Spot Price Forecast', simulation, forecast_url)
        chart_link2 = ChartLink('300 Cap', simulation, cap_url)
        chart_link3 = ChartLink('Spot Price Distribution', simulation, distribution_url)
        db.session.add(chart_link1)
        db.session.add(chart_link2)
        db.session.add(chart_link3)
        db.session.commit()

        return json_success(json.dumps({
            'email_to': email_to,
            'run_id': run_id,
            'sim_num': sim_num,
        }))

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
            item.end_date = get_full_week_end_date(item.start_date, item.end_date)
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
            item.end_date = get_full_week_end_date(item.start_date, item.end_date)
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
            os.remove(path)
            return jsonify({
                'message': message,
                'detail': detail
            })

    '''Set run_id after id is got'''
    def post_add(self, item):
        db.session.flush()
        g.id = item.id
        item.run_id = item.id + 10000
        db.session.commit()


    def prefill_hidden_field(self, form):
        flt_dic = self.get_filter_args()
        # print(form)
        if 'project' in flt_dic.keys():
            project = db.session.query(Project).filter_by(id=flt_dic['project']).one_or_none()
            form.project.data = project
        # generate unique uuid as run id
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
    @expose('/start_run/<id>/<run_type>/', methods=['GET', 'POST'])
    def start_run(self,id,run_type):
        simulation = db.session.query(Simulation).filter_by(id=id).one_or_none()

        if not simulation:
            message = 'No simulation found for this run id, please refresh the page and try again.'
            g.result = 'Run failed'
            g.detail = message
        else:
            g.action_object = simulation.name
            g.action_object_type = 'Simulation'
            if simulation.assumption.status == 'Error':
                g.result = 'Run failed'
                message = 'The assumption contains error, please reupload or use another one.'
                g.detail = message
            elif simulation.status == 'Running':
                g.result = 'Run failed'
                message = 'Running in progress, please wait till the run finish.'
                g.detail = message
            else:
                if simulation.assumption.s3_path is None:
                    path = get_s3_url(bucket_inputs, excel_path.format(simulation.assumption.name))
                    simulation.assumption.s3_path = path
                    db.session.commit()
                try:
                    data = request.form['duid_list']
                    data = data.strip('\t').replace('\n', '').split(',')
                    message = self.pre_run_check_process(simulation, run_type, duid_list=data)

                except Exception as e:
                    g.result = 'Run failed'
                    g.detail =repr(e)
                    message = 'Run failed: ' + repr(e)
                    traceback.print_exc()

        return jsonify({
            'message': message,
        })

    def pre_run_check_process(self, simulation, run_type, duid_list=[]):
        pass_check, message = check_assumption(simulation.assumption.s3_path, simulation.assumption.name, simulation)
        # pass_check, message = True, ''
        if pass_check:
            ref_day_generation_check(simulation, run_type)
            g.result = 'Started, pre-process in progress'
            if run_type == 'test':
                message = 'Test run started'
            else:
                message = 'Full run started'

            msg = {
                'excelKey': excel_path.format(simulation.assumption.name),
                'runNo': simulation.run_id,
                'processName': [],
                'bucket': bucket_inputs,
                'histBucket': bucket_hist,
                'startDate': '2017-01-01',
                'endDate': '2019-07-31',
                # 'simStartDate': '2020-01-01',
                'simStartDate': simulation.start_date.strftime('%Y-%m-%d'),
                'simEndDate': get_full_week_end_date(simulation.start_date, simulation.end_date).strftime('%Y-%m-%d'),
                # 'simEndDate': '2030-12-31',
                'runType': run_type,
                'supersetURL': get_current_external_ip(),
                'duids': duid_list,
                'email': g.user.email,
            }
            if not check_assumption_processed(simulation.run_id):
                if send_sqs_msg(json.dumps(msg)):
                    g.detail = json.dumps(msg)
                    simulation.status = 'Running'
                    db.session.commit()
                else:
                    g.result = 'Run failed'
                    message = 'Error sending to message to sqs, please try again later to contact dev team.'
                    g.detail = message
            else:
                simulation.status = 'Running'
                db.session.commit()
                g.result = 'Skip pre process to invocation'
                g.detail = 'Found existing assumption processed data, move to lambda invocation.'
                simulation_start_invoker.apply_async(args=[simulation.run_id, 5, msg])
        else:
            g.result = 'Run failed'
            g.detail = message
        return message

    @simulation_logger.log_simulation(action_name='process assumption')
    @expose('/process_success', methods=['GET', 'POST'])
    def process_success(self):
        print('receive process success')
        g.user = None
        data = json.loads(request.data.decode())
        run_id = data['runNo']
        simulation = db.session.query(Simulation).filter_by(run_id=run_id).first()

        simulation.assumption.status = 'Processed'
        g.action_object = simulation.assumption.name
        g.action_object_type = 'Assumption'
        g.result = 'Process success'
        db.session.commit()

        run_type = data['runType']
        if run_type == 'test':
            sim_num = 5
        else:
            # sim_num = simulation.run_no
            sim_num = 5
        simulation_start_invoker.apply_async(args=[run_id, sim_num])
        # flash('Simulation {} has finished the preprocess and is running now.'.format(simulation.name), 'info')
        return '200 OK'

    @simulation_logger.log_simulation(action_name='process assumption')
    @expose('/process_failed', methods=['GET', 'POST'])
    def process_failed(self):
        print('received process failed')
        g.user = None
        data = json.loads(request.data.decode())
        run_id = data['runNo']
        error_msg = data['procStatus']
        simulation = db.session.query(Simulation).filter_by(run_id=run_id).first()
        simulation.assumption.status = 'Error'
        simulation.assumption.status_detail = error_msg
        simulation.status = 'Run failed'
        simulation.status_detail = 'Error in pre-process for assumption file, please check the assumption detail.'
        # Find the latest log of start simulation to find the user who started the sim
        latest_sim = db.session.query(SimulationLog).filter_by(
            action_object_type='Simulation',
            action_object=simulation.name,
            action='start run',
            result='Started, pre-process in progress'
        ).order_by(SimulationLog.dttm.desc()).first()
        email_to = latest_sim.user.email
        message = {
            "sim_name": simulation.name,
            "assu_name": simulation.assumption.name,
            "error_log": error_msg,
        }

        if send_sendgrid_mail(email_to, message, 'd-3961c5296eed44eabd6d27ac1f14ccaf'):
            print('process failed email notification sent')
        g.action_object = simulation.assumption.name
        g.action_object_type = 'Assumption'
        g.result = 'Process failed'
        g.detail = error_msg
        db.session.commit()

        run_type = data['runType']
        if run_type == 'test':
            sim_num = 5
        else:
            # sim_num = simulation.run_no
            sim_num = 5
        # simulation_start_invoker.apply_async(args=[run_id, sim_num])
        # flash('The preprocess of simulation {} has failed, please check the log.'.format(simulation.name), 'danger')
        return '200 OK'

    @simulation_logger.log_simulation(action_name='query result')
    @expose('/query_success', methods=['GET', 'POST'])
    def query_success(self):
        g.user = None
        # flash('reached query success', 'info')
        data = json.loads(request.data.decode())
        # print(data)
        email = data['email']
        s3_list = ast.literal_eval(data['outS3Keys'])
        bucket = data['outBucket']
        run_id = data['sim_tag']
        simulation = db.query(Simulation).filter_by(run_id=run_id).first()
        attachments = []
        for s3_file in s3_list:
            path = tempfile.NamedTemporaryFile(
                dir=app.config["UPLOAD_FOLDER"], suffix='xlsx', delete=False
            ).name
            download_from_s3(bucket, s3_file, path)
            filename = s3_file.split('/')[-1]
            file_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            attachment = create_attachment(filename, path, file_type)
            attachments.append(attachment)
            os.remove(path)
        message = {
            'sim_name': simulation.name
            # 'sim_name': 'Run_196'
        }
        if send_sendgrid_mail(email, message, 'd-49e6d877ad7c440b84fe2b63835ccea5', attachments):
            g.result = 'query success'
            g.detail = repr(data)
        else:
            g.result = 'query success, message sent failed'
            g.detail = 'Failed to send email to {}'.format(email)
        return '200 OK'

    @simulation_logger.log_simulation(action_name='query result')
    @expose('/query_failed', methods=['GET', 'POST'])
    def query_failed(self):
        g.user = None
        data = json.loads(request.data.decode())
        # print(data)
        status_keys = ['s3Status', 'glueStats', 'crawlerStatus', 'msgSQS', 'queryId', 'queryStatus', 'updateStatus', 'exportStatus']
        for key in status_keys:
            if key in data.keys() and ('error' in data[key] or 'timeout' in data[key] or 'failure' in data[key]):
                error = f'{key} error: {data[key]}'
        g.result = 'query failed'
        g.detail = error
        return '200 OK'


    # @simulation_logger.log_simulation(action_name='start query')
    # @expose('/query_result/<sim_id>/', methods=['POST'])
    # def query_result(self, sim_id):
    #     query_sqs = 'https://sqs.ap-southeast-2.amazonaws.com/000581985601/sim_athena_queries'
    #     print('get query result')
    #     data = request.form['duid_list']
    #     data = data.strip('\t').replace('\n', '').split(',')
    #     simulation = db.session.query(Simulation).filter_by(id=sim_id).first()
    #     msg = {
    #         'sim_tag': simulation.run_id,
    #         # 'sim_tag': 'Run_196',
    #         'outBucket': bucket_inputs,
    #         'query_list': [
    #             'Technology_Generation_by_percentile_cal',
    #             'DUID_Generation_by_percentile_cal',
    #             'DUID_Average_Price_by_percentile_cal',
    #             'DUID_Revenue_by_percentile_cal',
    #             'DUID_Spot_Premium_by_percentile_cal',
    #             'TWA_Simulation_by_simulation_cal',
    #             'DUID_Generation_by_simulation_cal',
    #             'DUID_Average_Price_by_simulation_cal',
    #             'DUID_Revenue_by_simulation_cal'
    #         ],
    #         'dbname': 'dex_poc',
    #         'dispatchtbl': f'dispatch_{str(simulation.run_id).lower()}',
    #         # 'dispatchtbl': f'dispatch_{"Run_196".lower()}',
    #         'spottbl': f'spot_demand_{str(simulation.run_id).lower()}',
    #         # 'spottbl': f'spot_demand_{"Run_196".lower()}',
    #         'duids': data,
    #         'year_start': simulation.start_date.year,
    #         'year_end': get_full_week_end_date(simulation.start_date, simulation.end_date).year,
    #         'supersetURL': get_current_external_ip(),
    #         'email': g.user.email,
    #     }
    #     # if send_sqs_msg(msg, queue_url=query_sqs):
    #     g.action_object = simulation.name
    #     g.action_object_type = 'simulation'
    #     if send_sqs_msg(json.dumps(msg), queue_url=query_sqs):
    #         message = 'Query has been sent, the data files will be sent to your email when ready.'
    #         g.result = 'send query result'
    #         g.detail = json.dumps(msg)
    #     else:
    #         message = 'Query failed to send to sqs, please try again later or contact dev team.'
    #         g.result = 'send query result'
    #         g.detail=message
    #     return jsonify({'message': message})

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
        if item.simulations is not None and len(item.simulations) >0:
            g.direct_to_sub = True
            raise Exception('This project has modeling jobs associate with it. Please '
                            'delete the models first.')
        g.direct_to_sub = False

    def post_delete_redirect(self):
        if g.direct_to_sub:
            return redirect(url_for('SimulationModelView.list'))
        else:
            return redirect(url_for('.list'))

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
        if item.projects is not None and len(item.projects) >0:
            g.direct_to_sub = True
            raise Exception("This client has projects associate with it. Please delete "
                            "the projects first.")
        g.direct_to_sub = False

    def post_delete_redirect(self):
        if g.direct_to_sub:
            return redirect(url_for('ProjectModelView.list'))
        else:
            return redirect(url_for('.list'))

class SimulationLogModelView(SupersetModelView):
    route_base = "/simulationlog"
    datamodel = SQLAInterface(SimulationLog)
    include_route_methods = {RouteMethod.LIST, RouteMethod.SHOW, RouteMethod.INFO}

    list_columns = ['user', 'action', 'action_object', 'dttm', 'result']
    order_columns = ['user', 'action_object', 'action_object_type','dttm']

    base_order = ('dttm', 'desc')
    page_size = 20
