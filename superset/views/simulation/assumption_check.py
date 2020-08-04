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
import pandas as pd
import tempfile
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

from .forms import UploadISPForm
from .util import send_sqs_msg, get_current_external_ip
from .assumption_process import process_assumptions, upload_assumption_file, check_assumption, process_assumption_to_df_dict,\
    save_as_new_tab_version, ref_day_generation_check
from .util import get_redirect_endpoint, read_excel, read_csv, download_from_s3, get_full_week_end_date, from_dict, upload_stream_write
from ..utils import bootstrap_user_data, create_attachment

class UploadISPView(SimpleFormView):
    route_base = '/upload_isp'
    form_title = 'Upload ISP scencario'
    form = UploadISPForm
    form_template = "appbuilder/general/model/edit.html"

    def form_post(self, form):
        file_name = form.file.data.filename
        extension = os.path.splitext(file_name)[1].lower()
        path = tempfile.NamedTemporaryFile(
            dir=app.config["UPLOAD_FOLDER"], suffix=extension, delete=False
        ).name
        scenario = form.scenario.data
        source = form.source.data
        form.file.data.filename = path
        isp_case = form.isp_case.data
        g.action_object = isp_case
        g.action_object_type = 'Assumption'
        try:
            utils.ensure_path_exists(app.config["UPLOAD_FOLDER"])
            upload_stream_write(form.file.data, path)
            df = read_csv(path, names=['region', 'technology', 'year', 'value'])
            sub_tab_def = save_as_new_tab_version(db, df,
                                                  ISPCapacityDefinition, ISPCapacity,
                                                  note=isp_case, scenario=scenario,
                                                  isp_case=isp_case, source=source)
            # set relation of assumption def with sub table definition

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


class AssumptionBookModelView(
    SupersetModelView, DeleteMixin
):  # pylint: disable=too-many-ancestors
    route_base = "/assumption-book"
    default_view = 'comparison'
    datamodel = SQLAInterface(AssumptionDefinition)

    @expose("/comparison/")
    def comparison(self):
        username = g.user.username

        user = (
            db.session.query(ab_models.User).filter_by(username=username).one_or_none()
        )
        if not user:
            abort(404, description=f"User: {username} does not exist.")

        project_list_versions = db.session.query(ProjectListDefinition).all()
        project_list = [{'version' :project.Project_List_Version,
                         'note': project.Note} for project in project_list_versions]
        payload = {
            "user": bootstrap_user_data(user, include_perms=True),
            "projectList": project_list,
            "common": common_bootstrap_payload(),
        }

        return self.render_template(
            "superset/basic.html",
            entry="comparison",
            title=_("Edit Assumption"),
            bootstrap_data=json.dumps(
                payload, default=utils.pessimistic_json_iso_dttm_ser
            ),
        )

    @expose("/get-data/<state>/<technology>/<project_id>/<isp_case>/<isp_scen>/<isp_dev_path>/")
    def get_data(self, state, technology, project_id, isp_case, isp_scen, isp_dev_path=None):
        # form = request.form
        # topic =
        header, empower_data = self.get_project_list_data(state, technology, project_id)
        # Choose the latest version of the isp scenario
        isp_version = db.session.query(ISPCapacityDefinition).filter_by(isp_case=isp_case,scenario=isp_scen).order_by(
            ISPCapacityDefinition.id.desc()).first()
        tab_data = db.session.query(ISPCapacity).filter_by(isp_cap_def_id=isp_version.id, technology=technology, region=state[:-1]).all()
        isp_data = []
        for data_row in tab_data:
            isp_data.append(data_row.get_dict())

        empower_years = set()
        isp_years = set()
        empower_dict = dict()
        isp_dict = dict()
        for item in empower_data:
            empower_years.add(item['year'])
            empower_dict[item['year']] = item['value']

        for item in isp_data:
            isp_years.add(item['year'])
            isp_dict[item['year']] = item['value']

        years = sorted(empower_years.union(isp_years))

        empower_values = []
        isp_values = []
        for year in years:
            empower_values.append(empower_dict[year] if year in empower_dict else 0)
            isp_values.append(isp_dict[year] if year in isp_dict else 0)

        return jsonify(
            {'header': header,
             'years': years,
             'data': [
                 {'name': 'Empower', 'values': empower_values},
                 {'name': 'ISP', 'values': isp_values},
             ]}
        )


    def get_project_list_data(self, state, fuel_type, version):
        sql = "SELECT State as region, Fuel_Type as technology, YEAR(Start_Date) as year, SUM(Maximum_Quantity) as capacity, 'Empower' as source "\
                "FROM Project_List " \
                "WHERE State = :state and Fuel_Type = :fuel_type and Version = :version_id "\
                "GROUP BY region, technology, year " \
                "ORDER BY year desc"
        result = db.session.execute(sql, {"state": state, "fuel_type": fuel_type, "version_id": version})
        row_list = []
        for row in result:
            row_list.append(list(row))
        df = pd.DataFrame(row_list, columns=['region', 'technology','year','value', 'source'])
        df['value'] = df['value'].map(lambda x: float(x))
        max_year, min_year = df['year'].max(), df['year'].min()

        full_df = pd.DataFrame(columns=['year'])
        for index, year in zip(range(max_year-min_year+1), range(max_year, min_year-1, -1)):
            full_df.loc[index, 'year'] = year
        df = pd.merge(df, full_df, how='outer', on='year').sort_values('year', ascending=False)
        # Aggregate generation of each year starting from last year
        for index, row in df.iterrows():
            df.loc[index, 'region'] = state
            df.loc[index, 'tecnology'] = fuel_type
            df.loc[index, 'value'] = float(df[df['year'] <= row['year']]['value'].sum())
            df.loc[index, 'source'] = 'Empower'
        # Make region from xx1 to xx format
        df['region'] = df['region'].map(lambda x: x[:-1])
        return list(df.columns), df.sort_values('year').to_dict(orient='records')
