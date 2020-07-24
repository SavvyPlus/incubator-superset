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
