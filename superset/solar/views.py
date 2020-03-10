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
import os
import logging
import json
import requests
import stripe

from flask import flash, redirect, url_for, g, request, make_response, Markup, jsonify
from flask_appbuilder import has_access
from flask_babel import lazy_gettext
# from flask_mail import Mail, Message
from flask_login import login_user

from flask_appbuilder.views import expose, PublicFormView
from flask_appbuilder.security.forms import ResetPasswordForm
from .models import SolarBIUser, TeamRegisterUser, Plan
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .utils import set_session_team, update_mp_user, log_to_mp, send_sendgrid_email, sendgrid_email_sender


from .forms import (
    SolarBILoginForm_db,
    SolarBIPasswordRecoverForm,
    SolarBIPasswordRecoverFormWidget,
    SolarBIPasswordResetFormWidget,
    SolarBIPasswordResetForm,
    SolarBIUserInfoEditForm,
    SolarBIIUserInfoEditWidget,
    SolarBIResetMyPasswordWidget,
)
from flask_appbuilder._compat import as_unicode

from flask_appbuilder.security.views import AuthDBView, UserInfoEditView, ResetMyPasswordView


log = logging.getLogger(__name__)


class SolarBIAuthDBView(AuthDBView):
    invalid_login_message = lazy_gettext("Email/Username or password incorrect. Please try again.")
    # inactivated_login_message = lazy_gettext("Your account has not been activated yet. Please check your email.")
    inactivated_login_message = Markup("<span>Your account has not been activated yet. Please check your email.</span>"
                                       "<span class='resend-activation'>Not received the email?"
                                       "<a class='rae-btn'>Resend</a></span>")

    login_template = "appbuilder/general/security/solarbi_login_db.html"
    email_template = 'appbuilder/general/security/account_activation_mail.html'

    @expose("/login/", methods=["GET", "POST"])
    def login(self):
        if g.user is not None and g.user.is_authenticated:
            return redirect(self.appbuilder.get_url_for_index)
        form = SolarBILoginForm_db()
        if form.validate_on_submit():
            user = self.appbuilder.sm.auth_solarbi_user_db(
                form.username.data, form.password.data
            )
            if not user:
                # For team member, check if they have activated their accounts yet
                reg_user = self.appbuilder.get_session.query(TeamRegisterUser).\
                    filter_by(username=form.username.data).first()
                if not reg_user:
                    reg_user = self.appbuilder.get_session.query(TeamRegisterUser).\
                        filter_by(email=form.username.data).first()
                if reg_user:
                    flash(self.inactivated_login_message, "warning")
                    return redirect(self.appbuilder.get_url_for_login)

                flash(as_unicode(self.invalid_login_message), "warning")
                return redirect(self.appbuilder.get_url_for_login)

            # For team admin, check if they have activated their accounts
            curr_user = self.appbuilder.get_session.query(SolarBIUser).filter_by(username=form.username.data).first()
            if not curr_user:
                curr_user = self.appbuilder.get_session.query(SolarBIUser).filter_by(email=form.username.data).first()
            if curr_user and not curr_user.email_confirm:
                flash(self.inactivated_login_message, "warning")
                return redirect(self.appbuilder.get_url_for_login)

            remember = form.remember_me.data
            login_user(user, remember=remember)

            team = self.appbuilder.sm.find_team(user_id=g.user.id)
            for role in user.roles:
                if role.name == 'Admin':
                    return redirect(self.appbuilder.get_url_for_index)
            set_session_team(team.id, team.team_name)

            log_to_mp(user, team.team_name, 'login', {})

            return redirect(self.appbuilder.get_url_for_index)
        return self.render_template(
            self.login_template, title=self.title, form=form, appbuilder=self.appbuilder
        )

    @expose('/resend-activation', methods=['POST'])
    def resend_activation(self):
        user_email = request.json['user_email']
        register_user = self.appbuilder.sm.get_registered_user(user_email)
        if not register_user:
            return jsonify(dict(err="Sorry we cannot find the email"))

        if register_user.inviter is None:
            url = url_for('SolarBIRegisterUserDBView.activation',
                          _external=True,
                          activation_hash=register_user.registration_hash)
        else:
            url = url_for('SolarBIRegisterInvitationView.activate',
                          _external=True,
                          invitation_hash=register_user.registration_hash)

        dynamic_template_data = {
            'url': url,
            'first_name': register_user.first_name,
        }
        template_id = 'd-41d88127f1e14a28b1fedc2e0b456657'
        send_sendgrid_email(register_user, dynamic_template_data, template_id)
        flash(as_unicode('Successfully resend your activation'), 'info')
        return jsonify(dict(redirect='/'))


class SolarBIPasswordRecoverView(PublicFormView):
    """
        This is the view for recovering password
    """

    route_base = '/password-recover'

    email_template = 'appbuilder/general/security/password_recover_mail.html'
    """ The template used to generate the email sent to the user """

    email_subject = lazy_gettext('SolarBI - Reset Your Password')
    """ The email subject sent to the user """

    message = lazy_gettext('Password reset link sent to your email')
    """ The message shown on a successful registration """

    error_message = lazy_gettext('This email is not registered or confirmed yet.')
    """ The message shown on an unsuccessful registration """

    form = SolarBIPasswordRecoverForm
    edit_widget = SolarBIPasswordRecoverFormWidget
    form_template = 'appbuilder/general/security/recover_password_form_template.html'

    def send_sg_email(self, email, hash_val):
        message = Mail(
            from_email=sendgrid_email_sender,
            to_emails=email,
        )
        url = url_for('.reset', _external=True, reset_hash=hash_val)
        message.dynamic_template_data = {
            'url': url,
        }
        message.template_id = 'd-97dc2cd070a54380af4faf8aaaf85bb7'
        try:
            sendgrid_client = SendGridAPIClient(os.environ['SG_API_KEY'])
            _ = sendgrid_client.send(message)
            return True
        except Exception as e:
            log.error('Send email exception: {0}'.format(str(e)))
            return False

    def add_password_reset(self, email):
        reset_hash = self.appbuilder.sm.add_reset_request(email)
        if reset_hash is not None:
            flash(as_unicode(self.message), 'info')
            # self.send_email(email, reset_hash)
            self.send_sg_email(email, reset_hash)
            return redirect(self.appbuilder.get_url_for_index)
        else:
            flash(as_unicode(self.error_message), 'danger')
            return redirect(self.appbuilder.get_url_for_index)

    @expose('/reset/<string:reset_hash>')
    def reset(self, reset_hash):
        """ This is end point to verify the reset password hash from user
        """
        if reset_hash is not None:
            return redirect(self.appbuilder.sm.get_url_for_reset(token=reset_hash))

    def form_post(self, form):
        return self.add_password_reset(email=form.email.data)


class SolarBIResetPasswordView(PublicFormView):
    route_base = '/reset'
    form = SolarBIPasswordResetForm
    form_template = 'appbuilder/general/security/reset_password_form_template.html'
    edit_widget = SolarBIPasswordResetFormWidget
    redirect_url = '/'
    message = lazy_gettext('Password has been reset.')
    error_message = lazy_gettext('Sorry, the link has expired.')

    @expose('/form', methods=['GET'])
    def this_form_get(self):
        self._init_vars()
        form = self.form.refresh()
        token = request.args.get('token')
        user = self.appbuilder.sm.find_user_by_token(token)
        if user is not None:
            self.form_get(form)
            widgets = self._get_edit_widget(form=form)
            self.update_redirect()
            return self.render_template(self.form_template,
                                        title=self.form_title,
                                        widgets=widgets,
                                        appbuilder=self.appbuilder)
        flash(as_unicode(self.error_message), 'danger')
        return redirect(self.appbuilder.get_url_for_index)

    @expose('/form', methods=['POST'])
    def this_form_post(self):
        self._init_vars()
        form = self.form.refresh()
        if form.validate_on_submit():
            token = request.args.get('token')
            response = self.form_post(form, token=token)
            if not response:
                return self.this_form_get()
            return redirect(response)
        else:
            widgets = self._get_edit_widget(form=form)
            return self.render_template(
                self.form_template,
                title=self.form_title,
                widgets=widgets,
                appbuilder=self.appbuilder,
            )

    def form_post(self, form, **kwargs):
        token = kwargs['token']
        user = self.appbuilder.sm.find_user_by_token(token)

        if user is not None:
            flash(as_unicode(self.message), 'info')
            password = form.password.data
            self.appbuilder.sm.reset_password(user.id, password)
            self.appbuilder.sm.set_token_used(token)
            return self.appbuilder.get_url_for_index

        return None


class SolarBIUserInfoEditView(UserInfoEditView):
    form_title = 'My Profile - SolarBI'
    form = SolarBIUserInfoEditForm
    form_template = 'appbuilder/general/security/edit_user_info.html'
    edit_widget = SolarBIIUserInfoEditWidget
    sg = SendGridAPIClient(os.environ['SG_API_KEY'])
    headers = {'authorization': 'Bearer ' + os.environ['SG_API_KEY']}
    message = "Profile information has been successfully updated"

    def form_get(self, form):
        item = self.appbuilder.sm.get_user_by_id(g.user.id)
        # fills the form generic solution
        for key, value in form.data.items():
            if key == "csrf_token":
                continue

            if key == "subscription":
                contact_id = self.is_in_sg()
                user_in_sg = contact_id != -1
                # user_in_gs = self.user_in_gs(g.user.email)
                user_in_marketing_suppression = self.user_in_marketing_suppression(g.user.email)

                form_field = getattr(form, key)
                form_field.data = (user_in_sg and not user_in_marketing_suppression)
                continue

            form_field = getattr(form, key)
            form_field.data = getattr(item, key)

    @expose("/form", methods=["POST"])
    @has_access
    def this_form_post(self):
        self._init_vars()
        form = self.form.refresh()

        if form.validate_on_submit():
            response = self.form_post(form)
            if not response:
                return redirect("/solarbiuserinfoeditview/form")
            return response
        else:
            flash(as_unicode('The new email address has already been used.'), 'danger')
            return redirect('/solarbiuserinfoeditview/form')

    def form_post(self, form):
        self.message = "Profile information has been successfully updated"
        form = self.form.refresh(request.form)
        item = self.appbuilder.sm.get_user_by_id(g.user.id)

        if form.email.data != item.email:
            # If the user has been in SG already, delete it from contacts and marketing suppression group
            contact_id = self.is_in_sg()
            if contact_id != -1:
                self.delete_contact(contact_id)
                # self.delete_gs(item.email)
                self.delete_user_from_marketing_suppression(item.email)

            self.add_or_update_contact(form.email.data, form.first_name.data, form.last_name.data)
        else:
            contact_id = self.is_in_sg()
            is_in_sg = (contact_id != -1)
            if form.first_name.data != item.first_name or form.last_name.data != item.last_name:
                if contact_id != -1:
                    self.add_or_update_contact(form.email.data, form.first_name.data, form.last_name.data)

            # subscription_status = (is_in_sg and not self.user_in_gs(form.email.data))
            user_in_marketing_suppression = self.user_in_marketing_suppression(form.email.data)
            subscription_status = (is_in_sg and not user_in_marketing_suppression)
            if form.subscription.data != subscription_status:
                if form.subscription.data:
                    if self.user_in_marketing_suppression(form.email.data):
                        # self.delete_gs(form.email.data)
                        self.delete_user_from_marketing_suppression(form.email.data)
                    else:
                        self.add_or_update_contact(form.email.data, form.first_name.data, form.last_name.data)
                else:
                    # self.add_to_gs(form.email.data)
                    self.add_user_to_marketing_suppression(form.email.data)

        form.username.data = item.username
        form.populate_obj(item)
        self.appbuilder.sm.update_user(item)
        update_mp_user(g.user)

        # If current user is team admin, update the stripe email for his/her team.
        for team_role in g.user.team_role:
            if team_role.role.name == 'team_owner':
                logging.info('Updating email for team {}'.format(team_role.team.team_name))
                stripe.Customer.modify(team_role.team.stripe_user_id, email=g.user.email)

        flash(as_unicode(self.message), "info")

    def is_in_sg(self):
        # First check the 50 most recent changed contacts
        response1 = self.sg.client.marketing.lists._('823624d1-c51e-4193-8542-3904b7586c29?contact_sample=true').get()
        contact_sample = json.loads(response1.body.decode('utf-8'))['contact_sample']
        for contact in contact_sample:
            if g.user.email == contact['email']:
                return contact['id']

        response = self.sg.client.marketing.contacts.search.post(request_body={
            "query": "email LIKE '" + g.user.email + "' AND CONTAINS(list_ids, '823624d1-c51e-4193-8542-3904b7586c29')"
        })
        res = json.loads(response.body.decode("utf-8"))
        if not res['result']:
            return -1
        else:
            return res['result'][0]['id']

    def add_or_update_contact(self, email, first_name, last_name):
        _ = self.sg.client.marketing.contacts.put(request_body={
            "list_ids": [
                "823624d1-c51e-4193-8542-3904b7586c29"
            ],
            "contacts": [
                {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name
                }
            ]
        })
        # _ = json.loads(response.body.decode("utf-8"))

    def add_user_to_marketing_suppression(self, email):
        url = "https://api.sendgrid.com/v3/asm/groups/14067/suppressions"
        payload = "{\"recipient_emails\":[\"" + email + "\"]}"
        _ = requests.request("POST", url, data=payload, headers=self.headers)

    def delete_user_from_marketing_suppression(self, email):
        url = "https://api.sendgrid.com/v3/asm/groups/14067/suppressions/" + email
        _ = requests.request("DELETE", url, headers=self.headers)

    def user_in_marketing_suppression(self, email):
        url = "https://api.sendgrid.com/v3/asm/groups/14067/suppressions/search"
        payload = '{"recipient_emails":["' + email + '"]}'
        response = requests.request("POST", url, data=payload, headers=self.headers)
        if json.loads(response.text):
            return True
        else:
            return False

    def delete_contact(self, contact_id):
        self.sg.client.marketing.contacts.delete(query_params={"ids": contact_id})

    def user_in_gs(self, email):
        url = "https://api.sendgrid.com/v3/asm/suppressions/global/" + email
        response = requests.request("GET", url, headers=self.headers)
        if json.loads(response.text):
            return True
        else:
            return False

    def add_to_gs(self, email):
        url = "https://api.sendgrid.com/v3/asm/suppressions/global"
        payload = "{\"recipient_emails\":[\"" + email + "\"]}"
        _ = requests.request("POST", url, data=payload, headers=self.headers)

    def delete_gs(self, email):
        url = "https://api.sendgrid.com/v3/asm/suppressions/global/" + email
        _ = requests.request("DELETE", url, headers=self.headers)


class SolarBIResetMyPasswordView(ResetMyPasswordView):
    form_template = 'appbuilder/general/security/reset_my_password.html'
    edit_widget = SolarBIResetMyPasswordWidget
