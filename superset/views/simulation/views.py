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
import os
import tempfile
from flask import flash, redirect
from flask_appbuilder import expose, has_access, SimpleFormView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_babel import lazy_gettext as _

from superset import app, db
from superset.connectors.connector_registry import ConnectorRegistry
from superset.constants import RouteMethod
from superset.models.simulation import Assumption
from superset.utils import core as utils
from superset.views.base import check_ownership, DeleteMixin, SupersetModelView

from .forms import UploadAssumptionForm
from .assumption_process import process_assumptions

def upload_stream_write(form_file_field: "FileStorage", path: str):
    chunk_size = app.config["UPLOAD_CHUNK_SIZE"]
    with open(path, "bw") as file_description:
        while True:
            chunk = form_file_field.stream.read(chunk_size)
            if not chunk:
                break
            file_description.write(chunk)

class UploadAssumptionView(SimpleFormView):
    route_base = '/upload_assumption_file'
    form = UploadAssumptionForm
    form_template = "appbuilder/general/model/edit.html"
    form_title = "Upload assumption excel template"

    def form_post(self, form):
        print('uploaded success')

        excel_filename = form.excel_file.data.filename
        extension = os.path.splitext(excel_filename)[1].lower()
        path = tempfile.NamedTemporaryFile(
            dir=app.config["UPLOAD_FOLDER"], suffix=extension, delete=False
        ).name
        form.excel_file.data.filename = path
        name = form.name.data
        try:
            utils.ensure_path_exists(app.config["UPLOAD_FOLDER"])
            upload_stream_write(form.excel_file.data, path)
            process_assumptions(path, name)
            message = 'Upload success'
            assumption_file = db.session.query(Assumption).filter_by(name=form.name.data)
            if not assumption_file:
                assumption_file = Assumption()
                assumption_file.name = form.name.data
                assumption_file.s3_path = "s3://{}".format(form.name.data)
                db.session.add(assumption_file)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            message = str(e)

        flash(message, 'error')

        os.remove(path)

        # message = 'Upload success'

        return redirect('/upload_assumption_file/form')

class AssumptionModelView(SupersetModelView):
    route_base = "/assuptionmodelview"
    datamodel = SQLAInterface(Assumption)
    include_route_methods = {RouteMethod.LIST, RouteMethod.EDIT, RouteMethod.DELETE, RouteMethod.INFO, RouteMethod.SHOW}



class SimulationModelView(
    SupersetModelView
):
    route_base = "/simulation"

