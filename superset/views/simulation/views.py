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
import threading
import os
import tempfile
from flask import flash, redirect
from flask_appbuilder import expose, has_access, SimpleFormView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_babel import lazy_gettext as _

from superset import app, db
from superset.connectors.connector_registry import ConnectorRegistry
from superset.constants import RouteMethod
from superset.models.simulation import Assumption, Simulation
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
            thread = threading.Thread(target=self.handle_assumption_process, args=(path, name))
            thread.start()
            assumption_file = db.session.query(Assumption).filter_by(name=name).one_or_none()
            if not assumption_file:
                assumption_file = Assumption()
                assumption_file.name = name
                assumption_file.s3_path = "s3://{}".format(name)
                db.session.add(assumption_file)
            assumption_file.status = "Processing"
            db.session.commit()
            message = "Upload success"
            style = 'info'
        except Exception as e:
            message = "Upload failed:" + str(e)
            style = 'danger'
        os.remove(path)
        flash(message, style)
        # message = 'Upload success'

        return redirect('/upload_assumption_file/form')

    def handle_assumption_process(self, path, name):
        assumption_file = db.session.query(Assumption).filter_by(name=name).one_or_none()
        try:
            process_assumptions(path, name)
            assumption_file.status = "Uploaded"
            db.session.merge(assumption_file)
            db.session.commit()
        except Exception as e:
            assumption_file.status = "Error"
            assumption_file.status_detail = str(e)
            db.session.merge(assumption_file)
            db.session.commit()
            print(e)


class AssumptionModelView(SupersetModelView):
    route_base = "/assuptionmodelview"
    datamodel = SQLAInterface(Assumption)
    include_route_methods = {RouteMethod.LIST, RouteMethod.EDIT, RouteMethod.DELETE, RouteMethod.INFO, RouteMethod.SHOW}



class SimulationModelView(
    SupersetModelView
):
    route_base = "/simulationmodelview"
    datamodel = SQLAInterface(Simulation)
    include_route_methods = RouteMethod.CRUD_SET

