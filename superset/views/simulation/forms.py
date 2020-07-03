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
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, Select2Widget, DatePickerWidget, Select2ManyWidget
from flask_appbuilder.forms import DynamicForm
from flask_babel import lazy_gettext as _
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import BooleanField, IntegerField, SelectField, StringField, RadioField, DateField
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from superset.models.simulation import Assumption
from superset import app, db, security_manager
from superset.models import simulation as sim_models


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


class UploadAssumptionFormForStanding(DynamicForm):
    name = StringField(
        _("Name"),
        description=_("Name of the assumption file."),
        validators=[DataRequired()],
        widget=BS3TextFieldWidget(),
    )
    note = StringField(
        _("Description"),
        description=_("Note of the assumption"),
        widget=BS3TextFieldWidget(),
    )

    file = FileField(
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


class SimulationForm(DynamicForm):
    name = StringField(
        _("Name"),
        description=_("Name of the assumption file."),
        validators=[DataRequired()],
        widget=BS3TextFieldWidget(),
    )
    project = QuerySelectField(
        _("Project"),
        query_factory=lambda: db.session().query(sim_models.Project),
        allow_blank=False,
        widget=Select2Widget(),
        validators=[DataRequired()],
    )
    assumption = QuerySelectField(
        _("Assumption"),
        query_factory=lambda: db.session().query(sim_models.Assumption),
        allow_blank=False,
        widget=Select2Widget(),
        validators=[DataRequired()],
    )
    description = StringField(
        _("Description"),
        description=_("Description of the assumption"),
        widget=BS3TextFieldWidget(),
    )
    run_no = SelectField(
        _("Number of simulation run"),
        description=_("The number of simulations that requires to run"),
        choices=[
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
        ],
        widget=Select2Widget(),
        validators=[DataRequired()],
    )
    report_type = QuerySelectMultipleField(
        _("Report Type"),
        query_factory=lambda: db.session().query(sim_models.JobType),
        allow_blank=True,
        widget=Select2ManyWidget(),
    )
    start_date = DateField(
        _('Simulation start date'),
        description='Start date of simulation',
        widget=DatePickerWidget(),
    )
    end_date = DateField(
        _('Simulation end date'),
        description='End date of simulation',
        widget=DatePickerWidget()
    )




