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
# pylint: disable=C,R,W
from flask import g
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, BS3PasswordFieldWidget
from flask_babel import lazy_gettext
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from wtforms import (
    BooleanField, SelectField, StringField, PasswordField)
from wtforms.fields.html5 import EmailField

from flask_appbuilder.security.sqla.models import User, RegisterUser
from .models import Team, TeamRegisterUser
from flask_appbuilder.security.forms import DynamicForm
from flask_appbuilder.widgets import FormWidget, RenderTemplateWidget


def unique_required(form, field):
    from superset import db

    if field.name == "email":
        if db.session.query(User).filter_by(email=field.data).first() is not None:
            raise ValidationError("Email already exists")
        if db.session.query(TeamRegisterUser).filter_by(email=field.data).first() is not None:
            raise ValidationError("Email exists, waiting to be activated")

    if field.name == 'username':
        if db.session.query(User).filter_by(username=field.data).first() is not None:
            raise ValidationError("Username already exists")
        if db.session.query(TeamRegisterUser).filter_by(username=field.data).first() is not None:
            raise ValidationError("Username exists, waiting to be activated")

    if field.name == 'team':
        if db.session.query(Team).filter_by(team_name=field.data).first() is not None:
            raise ValidationError("Team name already exists")
        if db.session.query(TeamRegisterUser).filter_by(team=field.data).first() is not None:
            raise ValidationError("Team name already exists, waiting team admin to activate")


def non_existed_required(form, field):
    from superset import db

    if field.name == "email":
        if g.user.email != field.data:
            if db.session.query(User).filter_by(email=field.data).first() is not None:
                raise ValidationError("Email already exists")
            if db.session.query(TeamRegisterUser).filter_by(email=field.data).first() is not None:
                raise ValidationError("Email already exists")


class SolarBILoginForm_db(DynamicForm):
    username = StringField(lazy_gettext("User Name"), validators=[DataRequired()])
    password = PasswordField(lazy_gettext("Password"), validators=[DataRequired()])
    remember_me = BooleanField(lazy_gettext('remember me'), default=False)


class SolarBIRegisterUserDBForm(DynamicForm):
    first_name = StringField(
        lazy_gettext("First name"),
        validators=[DataRequired()],
    )
    last_name = StringField(
        lazy_gettext("Last name"),
        validators=[DataRequired()],
    )
    username = StringField(
        lazy_gettext("Username"),
        validators=[DataRequired(), unique_required],
    )
    email = StringField(
        lazy_gettext("Email"),
        validators=[DataRequired(), Email(), unique_required],
    )
    team = StringField(
        lazy_gettext("Team name"),
        validators=[DataRequired(),
                    Length(max=13, message="Team name cannot be longer than 13 characters"),
                    unique_required],
    )
    password = PasswordField(
        lazy_gettext("Password"),
        validators=[DataRequired()],
    )
    conf_password = PasswordField(
        lazy_gettext("Confirm Password"),
        validators=[EqualTo("password", message=lazy_gettext("Passwords must match"))],
    )


class SolarBIRegisterFormWidget(FormWidget):
    template = 'appbuilder/general/security/register_form.html'


class SolarBIPasswordRecoverForm(DynamicForm):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired(), Email()])


class SolarBIPasswordRecoverFormWidget(FormWidget):
    template = 'appbuilder/general/security/recover_password_form.html'


class SolarBIPasswordResetForm(DynamicForm):
    password = PasswordField(
        lazy_gettext("Password"),
        description=lazy_gettext(
            "Please use a good password policy,"
            " this application does not check this for you"
        ),
        validators=[DataRequired()],
    )
    conf_password = PasswordField(
        lazy_gettext("Confirm Password"),
        description=lazy_gettext("Please rewrite the password to confirm"),
        validators=[
            EqualTo("password", message=lazy_gettext("Passwords must match"))],
    )


class SolarBIPasswordResetFormWidget(FormWidget):
    template = 'appbuilder/general/security/reset_password_form.html'


class SolarBIRegisterInvitationForm(DynamicForm):
    team = StringField(lazy_gettext('Team name'), widget=BS3TextFieldWidget(), render_kw={'readonly': True})
    inviter = StringField(lazy_gettext('Inviter'), widget=BS3TextFieldWidget(), render_kw={'readonly': True})
    role = StringField(lazy_gettext('Role'), widget=BS3TextFieldWidget(), render_kw={'readonly': True})
    first_name = StringField(lazy_gettext('First Name'), validators=[DataRequired()], widget=BS3TextFieldWidget())
    last_name = StringField(lazy_gettext('Last Name'), validators=[DataRequired()], widget=BS3TextFieldWidget())
    username = StringField(lazy_gettext('Username'), validators=[DataRequired(), unique_required], widget=BS3TextFieldWidget())
    email = StringField(lazy_gettext('Email'), widget=BS3TextFieldWidget(), render_kw={'readonly': True})
    password = PasswordField(lazy_gettext('Password'),
                             description=lazy_gettext(
                                 'Please use a good password policy, this application does not check this for you'),
                             validators=[DataRequired()],
                             widget=BS3PasswordFieldWidget())
    conf_password = PasswordField(lazy_gettext('Confirm Password'),
                                  description=lazy_gettext('Please rewrite the password to confirm'),
                                  validators=[EqualTo('password', message=lazy_gettext('Passwords must match'))],
                                  widget=BS3PasswordFieldWidget())


class SolarBIRegisterInvitationUserDBForm(DynamicForm):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired(), Email()], widget=BS3TextFieldWidget())


class SolarBIDashboardListWidget(FormWidget):
    template = 'appbuilder/general/widgets/dashboard_list_widget.html'


class SolarBIListWidget(FormWidget):
    template = 'appbuilder/general/widgets/saved_list_widget.html'


class SolarBITeamFormWidget(FormWidget):
    template = 'appbuilder/general/widgets/add_member_form.html'


class SolarBIUserInfoEditForm(DynamicForm):
    first_name = StringField(
        lazy_gettext("First Name"),
        validators=[DataRequired()],
        widget=BS3TextFieldWidget(),
        description=lazy_gettext("Write the user first name or names"),
    )
    last_name = StringField(
        lazy_gettext("Last Name"),
        validators=[DataRequired()],
        widget=BS3TextFieldWidget(),
        description=lazy_gettext("Write the user last name"),
    )
    email = StringField(
        lazy_gettext("Email"),
        validators=[DataRequired(), non_existed_required],
        widget=BS3TextFieldWidget(),
        description=lazy_gettext("Write the user last name"),
    )
    username = StringField(
        lazy_gettext("Username (readonly)"),
        widget=BS3TextFieldWidget(),
        render_kw={'disabled': True},
    )
    subscription = BooleanField(lazy_gettext('Email product updates and news?'), default=False)


class SolarBIIUserInfoEditWidget(RenderTemplateWidget):
    template = 'appbuilder/general/widgets/edit_user_info_widget.html'


class SolarBIResetMyPasswordWidget(RenderTemplateWidget):
    template = 'appbuilder/general/widgets/reset_my_password_widget.html'


class SolarBIInvitationWidget(RenderTemplateWidget):
    template = 'appbuilder/general/widgets/invitation_widget.html'