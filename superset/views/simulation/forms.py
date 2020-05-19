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
"""Contains the logic to create cohesive forms on the explore view"""
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, Select2Widget
from flask_appbuilder.forms import DynamicForm
from flask_babel import lazy_gettext as _
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import BooleanField, IntegerField, SelectField, StringField, RadioField, DateField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from superset.models.simulation import Assumption
from superset import app, db, security_manager
from superset.forms import CommaSeparatedListField, filter_not_empty_values
from superset.models import core as models

class UploadAssumptionForm(DynamicForm):

    name = StringField(
        _("Name"),
        description=_("Name of the assumption file."),
        validators=[DataRequired()],
        widget=BS3TextFieldWidget(),
    )
    description = StringField(
        _("Description"),
        description=_("Description of the assumption"),
        widget=BS3TextFieldWidget(),
    )

    download_link = FileField(
        _("Excel File"),
        description=_("Select the assumption template excel file."),
        validators=[
            FileRequired(),
            FileAllowed(
                ["xlsx"],
                _(
                    "Only the following file extensions are allowed: "
                    "%(allowed_extensions)s",
                    allowed_extensions=", ".join(["xlsx"]),
                ),
            ),
        ],
    )

def possible_assumptions():
    # from flask_appbuilder.models.sqla.interface import SQLAInterface
    return Assumption.query

class AddSimulationForm(DynamicForm):
    assumption_choice1 = QuerySelectField(
        _("assumption choice 1"),
        query_factory=possible_assumptions,
        get_label='name_en', get_pk=lambda a: a.id,
        description=_("Name of the assumption file."),
    )
    assumption_choice2 = FileField(
        _("Excel File"),
        description=_("Select the assumption template excel file."),
        validators=[
            FileAllowed(
                ["xlsx"],
                _(
                    "Only the following file extensions are allowed: "
                    "%(allowed_extensions)s",
                    allowed_extensions=", ".join(["xlsx"]),
                ),
            ),
        ],
    )
    name = StringField(
        _("Name"),
        description=_("Name of the assumption file."),
        validators=[DataRequired()],
        widget=BS3TextFieldWidget(),
    )
    description = StringField(
        _("Description"),
        description=_("Description of the assumption"),
    )
    start_date = DateField('Simulation start date', description='Start date of simulation')
    end_date = DateField('Simulation end date', description='End date of simulation')
    run_id = StringField(
        'Run ID',
        description='Run id, must be integer',
        validators=[DataRequired()]
    )
    generation_model = StringField(
        'Generation model',
        description='The generation model'
    )
    run_no = StringField(
        'Number of simulation runs',
        description='The number of simulations that requires to run',
        validators=[DataRequired()]
    )
    report_type = StringField(
        'Report type',
        description='The type the report, it determines the type of chart for final data'
    )




