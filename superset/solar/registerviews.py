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
import json
import time
import logging
import stripe

from flask import flash, redirect, url_for, g, request, make_response, jsonify, session
from flask_babel import lazy_gettext
# from flask_mail import Mail, Message

from flask_appbuilder._compat import as_unicode
from flask_appbuilder import const as c, has_access
from flask_appbuilder.validators import Unique
from flask_appbuilder.views import expose
from flask_appbuilder.security.registerviews import RegisterUserDBView, BaseRegisterUser
from flask_login import login_user

from .forms import (
    SolarBIRegisterFormWidget, SolarBIRegisterUserDBForm, SolarBIRegisterInvitationForm,
    SolarBIRegisterInvitationUserDBForm, SolarBITeamFormWidget, SolarBIInvitationWidget,
)
from .models import SolarBIUser, Plan
from .utils import post_request, get_session_team, set_session_team, log_to_mp, free_credit_in_dollar, send_sendgrid_email
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

log = logging.getLogger(__name__)


class SolarBIRegisterUserDBView(RegisterUserDBView):
    # mc_client = MailChimp(mc_api=os.environ['MC_API_KEY'], mc_user='solarbi')
    sg = SendGridAPIClient(os.environ['SG_API_KEY'])
    form = SolarBIRegisterUserDBForm
    edit_widget = SolarBIRegisterFormWidget
    form_template = 'appbuilder/general/security/register_form_template.html'
    email_subject = 'SolarBI - Team Created Confirmation'
    email_template = 'appbuilder/general/security/account_activation_mail.html'

    @expose('/activation/<string:activation_hash>')
    def activation(self, activation_hash):
        """
            Endpoint to expose an activation url, this url
            is sent to the user by email, when accessed the user is inserted
            and activated
        """
        reg = self.appbuilder.sm.find_register_user(activation_hash)
        if not reg:
            log.error(c.LOGMSG_ERR_SEC_NO_REGISTER_HASH.format(activation_hash))
            flash(as_unicode(self.false_error_message), 'danger')
            return redirect(self.appbuilder.get_url_for_index)

        # Automatically confirm the user email
        user = self.appbuilder.get_session.query(SolarBIUser).filter_by(email=reg.email).first()
        user.email_confirm = True

        team_reg = self.appbuilder.sm.add_team(user, reg.team, reg.registration_date)
        # self.handle_aws_info(org_reg, user)
        self.appbuilder.sm.del_register_user(reg)

        _ = self.sg.client.marketing.contacts.put(request_body={
            "list_ids": [
                "823624d1-c51e-4193-8542-3904b7586c29"
            ],
            "contacts": [
                {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            ]
        })
        # if user.login_count is None or user.login_count == 0:
        #     is_first_login = True
        # else:
        #     is_first_login = False

        # Register stripe user for the team using user's email
        # self.appbuilder.sm.create_stripe_user_and_sub(user, team_reg)
        self.appbuilder.sm.update_user_auth_stat(user, True)
        login_user(user)

        log_to_mp(user, team_reg.team_name, 'login', {})

        set_session_team(team_reg.id, team_reg.team_name)
        self.appbuilder.get_session.commit()
        flash(as_unicode('Your account has been successfully activated!'), 'success')
        return redirect(self.appbuilder.get_url_for_index)

    def add_form_unique_validations(self, form):
        datamodel_user = self.appbuilder.sm.get_user_datamodel
        datamodel_register_user = self.appbuilder.sm.get_register_user_datamodel
        if len(form.email.validators) == 2:
            form.email.validators.append(Unique(datamodel_user, 'email'))
            form.email.validators.append(Unique(datamodel_register_user, 'email'))

    def send_sg_email(self, register_user):
        url = url_for(
            ".activation",
            _external=True,
            activation_hash=register_user.registration_hash,
        )
        dynamic_template_data = {
            'url': url,
            'first_name': register_user.first_name,
        }
        template_id = 'd-41d88127f1e14a28b1fedc2e0b456657'
        return send_sendgrid_email(register_user, dynamic_template_data, template_id)

    def add_registration_team_admin(self, **kwargs):
        """
            Add a registration request for the user.
        :rtype : TeamRegisterUser
        """

        register_user = self.appbuilder.sm.add_register_user_team_admin(**kwargs)
        if register_user:
            user = self.appbuilder.sm.add_user(username=register_user.username,
                                               email=register_user.email,
                                               first_name=register_user.first_name,
                                               last_name=register_user.last_name,
                                               role=self.appbuilder.sm.find_role('team_owner'),
                                               hashed_password=register_user.password)
            if not user:
                flash(as_unicode(self.error_message), 'danger')
                self.appbuilder.sm.del_register_user_and_user(register_user)
                return None

            if self.send_sg_email(register_user):
                flash(as_unicode(lazy_gettext("Register success! An activation email has been sent to you.")), 'info')
                return register_user
            else:
                flash(as_unicode(self.error_message), 'danger')
                self.appbuilder.sm.del_register_user_and_user(register_user)
                return None

    def form_post(self, form):
        self.add_form_unique_validations(form)
        self.add_registration_team_admin(first_name=form.first_name.data,
                                         last_name=form.last_name.data,
                                         username=form.username.data,
                                         email=form.email.data,
                                         password=form.password.data,
                                         team=form.team.data)

    def get_redirect(self):
        return self.appbuilder.get_url_for_index


class SolarBICreditRegisterView(SolarBIRegisterUserDBView):
    route_base = '/credit-register'

    @expose('/activation/<string:activation_hash>')
    def activation(self, activation_hash):
        """
            Endpoint to expose an activation url, this url
            is sent to the user by email, when accessed the user is inserted
            and activated
        """
        reg = self.appbuilder.sm.find_register_user(activation_hash)
        if not reg:
            log.error(c.LOGMSG_ERR_SEC_NO_REGISTER_HASH.format(activation_hash))
            flash(as_unicode(self.false_error_message), 'danger')
            return redirect(self.appbuilder.get_url_for_index)

        # Automatically confirm the user email
        user = self.appbuilder.get_session.query(SolarBIUser).filter_by(email=reg.email).first()
        user.email_confirm = True
        self.appbuilder.get_session.commit()

        team_reg = self.appbuilder.sm.add_team(user, reg.team, reg.registration_date, credit=int(free_credit_in_dollar) *
                                                                                             100)
        # self.handle_aws_info(org_reg, user)
        self.appbuilder.sm.del_register_user(reg)

        _ = self.sg.client.marketing.contacts.put(request_body={
            "list_ids": [
                "823624d1-c51e-4193-8542-3904b7586c29"
            ],
            "contacts": [
                {
                    "email": reg.email,
                    "first_name": reg.first_name,
                    "last_name": reg.last_name
                }
            ]
        })
        # if user.login_count is None or user.login_count == 0:
        #     is_first_login = True
        # else:
        #     is_first_login = False

        # Register stripe user for the team using user's email
        # self.appbuilder.sm.create_stripe_user_and_sub(user, team_reg)

        self.appbuilder.sm.update_user_auth_stat(user, True)
        login_user(user)

        log_to_mp(user, team_reg.team_name, 'login', {})

        set_session_team(team_reg.id, team_reg.team_name)

        flash(as_unicode('Your account has been successfully activated!'), 'success')
        return redirect(self.appbuilder.get_url_for_index)


class SolarBITrialRegisterView(SolarBIRegisterUserDBView):
    route_base = '/trial-register'

    @expose('/activation/<string:activation_hash>')
    def activation(self, activation_hash):
        """
            Endpoint to expose an activation url, this url
            is sent to the user by email, when accessed the user is inserted
            and activated
        """
        reg = self.appbuilder.sm.find_register_user(activation_hash)
        if not reg:
            log.error(c.LOGMSG_ERR_SEC_NO_REGISTER_HASH.format(activation_hash))
            flash(as_unicode(self.false_error_message), 'danger')
            return redirect(self.appbuilder.get_url_for_index)

        # Automatically confirm the user email
        user = self.appbuilder.get_session.query(SolarBIUser).filter_by(email=reg.email).first()
        user.email_confirm = True
        self.appbuilder.get_session.commit()

        # Start with starter plan trial
        plan = self.appbuilder.get_session().query(Plan).filter_by(id=2).first()
        team_reg = self.appbuilder.sm.add_team(user, reg.team, reg.registration_date, plan_id=plan.id, trial_days=14)
        # self.handle_aws_info(org_reg, user)
        self.appbuilder.sm.del_register_user(reg)

        _ = self.sg.client.marketing.contacts.put(request_body={
            "list_ids": [
                "823624d1-c51e-4193-8542-3904b7586c29"
            ],
            "contacts": [
                {
                    "email": reg.email,
                    "first_name": reg.first_name,
                    "last_name": reg.last_name
                }
            ]
        })
        # if user.login_count is None or user.login_count == 0:
        #     is_first_login = True
        # else:
        #     is_first_login = False

        # Register stripe user for the team using user's email
        # self.appbuilder.sm.create_stripe_user_and_sub(user, team_reg)

        self.appbuilder.sm.update_user_auth_stat(user, True)
        login_user(user)

        log_to_mp(user, team_reg.team_name, 'login', {})

        set_session_team(team_reg.id, team_reg.team_name)

        flash(as_unicode('Your account has been successfully activated!'), 'success')
        return redirect(self.appbuilder.get_url_for_index)


class SolarBIRegisterInvitationUserDBView(RegisterUserDBView):
    redirect_url = '/'
    route_base = '/solar'
    form = SolarBIRegisterInvitationUserDBForm
    form_title = 'Team - SolarBI'
    form_template = 'appbuilder/general/security/team_form_template.html'
    msg = 'Invitation has been sent to the email.'
    email_subject = 'You are invited to join SolarBI'
    email_template = 'appbuilder/general/security/team_member_invitation_mail.html'
    edit_widget = SolarBITeamFormWidget

    def send_sg_email(self, register_user, existed=False):
        """
            Method for sending the registration Email to the user
        """
        if existed:
            dynamic_template_data = {
                'invited_first': register_user.first_name,
                'invited_last': register_user.last_name,
                'team_name': get_session_team(self.appbuilder.sm, g.user.id)[1],
                'team_admin_first': g.user.first_name,
                'team_admin_last': g.user.last_name,
            }
            template_id = 'd-3904a5fe60184bb3a99ebed1664f924a'
        else:
            url = self.appbuilder.sm.get_url_for_invitation(register_user.registration_hash)
            dynamic_template_data = {
                'url': url,
                'team_name': register_user.team,
            }
            template_id = 'd-58f22673cff740019dd94fa9d118b73a'
        return send_sendgrid_email(register_user, dynamic_template_data, template_id)

    def add_form_unique_validations(self, form):
        datamodel_user = self.appbuilder.sm.get_user_datamodel
        datamodel_register_user = self.appbuilder.sm.get_register_user_datamodel
        if len(form.email.validators) == 2:
            form.email.validators.append(Unique(datamodel_user, 'email'))
            form.email.validators.append(Unique(datamodel_register_user, 'email'))

    def remove_email_unique_validation(self, form):
        email_field = form.email
        for validator in email_field.validators:
            if type(validator).__name__ == 'Unique':
                email_field.validators.remove(validator)

    @expose('/my-team', methods=['GET'])
    @has_access
    def invitation(self):
        self._init_vars()
        form = self.form.refresh()
        team_id, team_name = get_session_team(self.appbuilder.sm, g.user.id)
        team = self.appbuilder.sm.find_team(team_id=team_id)
        # form.role.choices = self.appbuilder.sm.find_invite_roles(g.user.id)
        awaiting_emails = self.appbuilder.sm.get_awaiting_emails(team)
        team_members = self.appbuilder.sm.get_team_members(team.id)
        widgets = self._get_edit_widget(form=form)
        self.update_redirect()
        self.add_form_unique_validations(form)
        return self.render_template(self.form_template,
                                    team_name=team.team_name,
                                    team_members=team_members,
                                    awaiting_emails=awaiting_emails,
                                    title=self.form_title,
                                    widgets=widgets,
                                    appbuilder=self.appbuilder
                                    )

    @expose('/my-team', methods=['POST'])
    @has_access
    def invitation_post(self):
        form = self.form.refresh()
        # self.add_form_unique_validations(form)
        self.remove_email_unique_validation(form)

        # choices placeholder to pass validation
        # form.role.choices = self.appbuilder.sm.find_invite_roles(g.user.id)
        role_id = self.appbuilder.sm.find_solar_default_role_id().id
        if form.validate_on_submit():
            user_id = g.user.id
            try:
                team = self.appbuilder.sm.find_team(team_id=get_session_team(self.appbuilder.sm, g.user.id)[0])

                # Check if the invited user is already in the team
                for existed_user in team.users:
                    if existed_user.email == form.email.data:
                        flash(as_unicode('User already in the team'), 'danger')
                        return redirect('/solar/my-team')

                reg_user, existed = self.appbuilder.sm.add_invite_register_user(email=form.email.data, team=team,
                                                                                role=role_id, inviter=user_id)
                if reg_user:
                    if self.send_sg_email(reg_user, existed):
                        if not existed:
                            flash(as_unicode('Invitation sent to %s' % form.email.data), 'info')
                        else:
                            flash(as_unicode('%s is an existed user. Added to your team' % form.email.data), 'info')
                        return redirect('/solar/my-team')
                    else:
                        self.appbuilder.sm.delete_invited_user(user_email=form.email.data)
                        flash(as_unicode('Cannot send invitation to user'), 'danger')
                        return redirect('/solar/my-team')
            except Exception as e:
                flash(as_unicode(e), 'danger')
                return redirect('/solar/my-team')
        else:
            flash(as_unicode('Invalid email'), 'danger')
            return redirect('/solar/my-team')

    @expose('/update-team-name', methods=['POST'])
    def update_team_name(self):
        new_team_name = request.json['new_team_name']
        if self.appbuilder.sm.find_team(team_name=new_team_name) is not None:
            return jsonify(dict(err='Team name exists'))

        if self.appbuilder.sm.update_team_name(g.user.id, new_team_name):
            team = self.appbuilder.sm.find_team(team_id=get_session_team(self.appbuilder.sm, g.user.id)[0])
            stripe.Customer.modify(team.stripe_user_id, description=new_team_name)

            flash(as_unicode('Successfully update the team name'), 'info')
            return jsonify(dict(redirect='/solar/my-team'))

    @expose('/create-team/', methods=['POST'])
    def create_team(self):
        team_name = request.json['team_name']
        if self.appbuilder.sm.find_team(team_name=team_name) is not None:
            return json.dumps({'msg': 'Team name existed'})

        new_team = self.appbuilder.sm.add_team(g.user, team_name)
        if new_team:
            set_session_team(new_team.id, new_team.team_name)
            flash(as_unicode('Successfully create team {}'.format(new_team.team_name)), 'info')
            return jsonify(dict(redirect='/solar/my-team'))
        else:
            flash(as_unicode('Unable to create team'), 'danger')
            return jsonify(dict(redirect='/solar/my-team'))

    @expose('/send-invitation', methods=['POST'])
    def send_invitation(self):
        user_email = request.json['selected_email']
        role_id = self.appbuilder.sm.find_solar_default_role_id().id

        if user_email:
            user_id = g.user.id
            try:
                team = self.appbuilder.sm.find_team(team_id=get_session_team(self.appbuilder.sm, user_id)[0])
                # Check if the invited user is already in the team
                for existed_user in team.users:
                    if existed_user.email == user_email:
                        flash(as_unicode('User already in the team'), 'danger')
                        return jsonify(dict(redirect='/solar/dashboard'))

                if self.appbuilder.sm.get_registered_user(user_email):
                    flash(as_unicode('You have already send invitation to the user'), 'danger')
                    return jsonify(dict(redirect='/solar/dashboard'))

                reg_user, existed = self.appbuilder.sm.add_invite_register_user(email=user_email, team=team,
                                                                                role=role_id, inviter=user_id)
                if reg_user:
                    if self.send_sg_email(reg_user, existed):
                        if not existed:
                            flash(as_unicode('Invitation sent to %s' % user_email), 'info')
                        else:
                            flash(as_unicode('%s is an existed user. Added to your team' % user_email), 'info')
                        return jsonify(dict(redirect='/solar/dashboard'))
                    else:
                        self.appbuilder.sm.delete_invited_user(user_email=user_email)
                        flash(as_unicode('Cannot send invitation to user'), 'danger')
                        return jsonify(dict(redirect='/solar/dashboard'))
            except Exception as e:
                flash(as_unicode(e), 'danger')
                return jsonify(dict(redirect='/solar/dashboard'))
        else:
            flash(as_unicode('Invalid email'), 'danger')
            return jsonify(dict(redirect='/solar/dashboard'))

    @expose('/resend-email', methods=['POST'])
    def resend_email(self):
        user_email = request.json['selected_email']
        # First delete the current invitation
        self.appbuilder.sm.delete_invited_user(user_email=user_email)
        # Then send a new and updated invitation link
        role_id = self.appbuilder.sm.find_solar_default_role_id().id
        team = self.appbuilder.sm.find_team(team_id=get_session_team(self.appbuilder.sm, g.user.id)[0])
        reg_user, existed = self.appbuilder.sm.add_invite_register_user(email=user_email,
                                                                        team=team,
                                                                        role=role_id,
                                                                        inviter=g.user.id)
        if reg_user:
            if self.send_sg_email(reg_user, existed):
                flash(as_unicode('Resend invitation to %s' % user_email), 'info')
                return jsonify(dict(redirect='/solar/my-team'))
            else:
                flash(as_unicode('Cannot resend invitation to user'), 'danger')
                return jsonify(dict(redirect='/solar/my-team'))

        # reg_user = self.appbuilder.sm.get_registered_user(user_email)
        # self.send_email(reg_user)
        # flash(as_unicode('Resend invitation to %s' % user_email), 'info')
        return jsonify(dict(redirect='/solar/my-team'))

    @expose('/delete-invitation', methods=['POST'])
    def delete_invitation(self):
        user_email = request.json['selected_email']
        self.appbuilder.sm.delete_invited_user(user_email=user_email)
        flash(as_unicode('Invitation to %s has been removed' % user_email), 'info')
        return jsonify(dict(redirect='/solar/my-team'))


class SolarBIRegisterInvitationView(BaseRegisterUser):
    # mc_client = MailChimp(mc_api=os.environ['MC_API_KEY'], mc_user='solarbi')
    sg = SendGridAPIClient(os.environ['SG_API_KEY'])
    activation_message = lazy_gettext("Register successfully! An activation email has been sent to you")
    error_message = lazy_gettext("Username or Email already existed")
    form = SolarBIRegisterInvitationForm
    form_template = 'appbuilder/general/security/invitation_registration.html'
    activation_template = 'appbuilder/general/security/activation.html'
    edit_widget = SolarBIInvitationWidget

    email_template = 'appbuilder/general/security/account_activation_mail.html'
    email_subject = 'SolarBI - Team Member Activation'

    # def send_email(self, register_user):
    #     """
    #         Method for sending the registration Email to the user
    #     """
    #     mail = Mail(self.appbuilder.get_app)
    #     msg = Message()
    #     msg.sender = 'SolarBI', 'no-reply@solarbi.com.au'
    #     msg.subject = self.email_subject
    #     url = url_for('.activate', _external=True, invitation_hash=register_user.registration_hash)
    #     msg.html = self.render_template(self.email_template,
    #                                     url=url,
    #                                     username=register_user.username,
    #                                     team_name=register_user.team)
    #     msg.recipients = [register_user.email]
    #     try:
    #         mail.send(msg)
    #     except Exception as e:
    #         log.error('Send email exception: {0}'.format(str(e)))
    #         return False
    #     return True

    def send_sg_email(self, register_user):
        url = url_for('.activate', _external=True, invitation_hash=register_user.registration_hash)
        dynamic_template_data = {
            'url': url,
            'first_name': register_user.first_name,
        }
        template_id = 'd-41d88127f1e14a28b1fedc2e0b456657'
        return send_sendgrid_email(register_user, dynamic_template_data, template_id)

    @expose('/invitation/<string:invitation_hash>', methods=['GET'])
    def invitation(self, invitation_hash):
        """End point for registration by invitation"""
        self._init_vars()
        form = self.form.refresh()
        # Find team inviter and email by invitation hash
        team_name, inviter, email, role = \
            self.appbuilder.sm.find_invite_hash(invitation_hash)
        if email is not None:
            form.email.data = email
            form.team.data = team_name
            form.inviter.data = inviter
            form.role.data = role
            widgets = self._get_edit_widget(form=form)
            self.update_redirect()
            return self.render_template(self.form_template,
                                        title=self.form_title,
                                        widgets=widgets,
                                        appbuilder=self.appbuilder)
        else:
            flash('This link has been used or expired. Please contact your team admin', 'danger')

        return redirect(self.appbuilder.get_url_for_index)

    def edit_invited_register_user(self, form, invitation_hash):
        register_user = self.appbuilder.sm.edit_invite_register_user_by_hash(invitation_hash,
                                                                             first_name=form.first_name.data,
                                                                             last_name=form.last_name.data,
                                                                             username=form.username.data,
                                                                             password=form.password.data,)
        if register_user and self.send_sg_email(register_user):
            flash(as_unicode(self.activation_message), 'info')
            return self.appbuilder.get_url_for_index
        else:
            flash(as_unicode(self.error_message), 'danger')
            # self.appbuilder.sm.del_register_user(register_user)
            return None

    @expose('/invitation/<string:invitation_hash>', methods=['POST'])
    def invite_register(self, invitation_hash):
        """End point for registration by invitation"""
        form = self.form.refresh()

        if form.validate_on_submit() and self.appbuilder.sm.find_register_user(invitation_hash):
            response = self.edit_invited_register_user(form, invitation_hash)
            if not response:
                # flash(as_unicode(self.error_message), 'danger')
                return redirect(self.appbuilder.get_url_for_index)
            return redirect(response)
        else:
            flash(as_unicode(self.error_message), 'danger')
            widgets = self._get_edit_widget(form=form)
            return self.render_template(
                self.form_template,
                title=self.form_title,
                widgets=widgets,
                appbuilder=self.appbuilder,
            )

    @expose('/activate/<string:invitation_hash>')
    def activate(self, invitation_hash):
        reg = self.appbuilder.sm.find_register_user(invitation_hash)
        if not reg:
            flash(as_unicode(self.false_error_message), 'danger')
            return redirect(self.appbuilder.get_url_for_index)

        # self.mc_client.lists.members.create(list_id='c257103535', data={
        #     'email_address': reg.email,
        #     'status': 'subscribed',
        #     'merge_fields': {
        #         'FNAME': reg.first_name,
        #         'LNAME': reg.last_name,
        #     },
        # })
        _ = self.sg.client.marketing.contacts.put(request_body={
            "list_ids": [
                "823624d1-c51e-4193-8542-3904b7586c29"
            ],
            "contacts": [
                {
                    "email": reg.email,
                    "first_name": reg.first_name,
                    "last_name": reg.last_name
                }
            ]
        })
        if not self.appbuilder.sm.add_team_user(email=reg.email,
                                                first_name=reg.first_name,
                                                last_name=reg.last_name,
                                                username=reg.username,
                                                role_id=reg.role_assigned,
                                                team=reg.team,
                                                hashed_password=reg.password):
            flash(as_unicode(self.error_message), 'danger')
            return redirect(self.appbuilder.get_url_for_index)
        else:
            self.appbuilder.sm.del_register_user(reg)
            return self.render_template(self.activation_template,
                                        username=reg.email,
                                        first_name=reg.first_name,
                                        last_name=reg.last_name,
                                        appbuilder=self.appbuilder)