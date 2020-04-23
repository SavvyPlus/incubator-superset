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
import datetime
import logging
import random
import string
import stripe
import os
import uuid

from flask import url_for
from flask_appbuilder import const, urltools
from flask_appbuilder.models.sqla.interface import SQLAInterface
from werkzeug.security import generate_password_hash, check_password_hash

from superset.solar.views import SolarBIPasswordRecoverView, SolarBIAuthDBView, \
    SolarBIResetPasswordView, SolarBIUserInfoEditView, SolarBIResetMyPasswordView
from superset.solar.registerviews import (
    SolarBIRegisterUserDBView, SolarBIRegisterInvitationView,
    SolarBIRegisterInvitationUserDBView,
    SolarBICreditRegisterView,
    SolarBITrialRegisterView
)
from superset.solar.models import Plan, ResetRequest, Team, TeamRegisterUser, TeamSubscription, SolarBIUser, TeamRole
from superset.security import SupersetSecurityManager

from .utils import get_session_team, set_session_team, log_to_mp, create_mp_team, update_mp_user, mp_add_user_to_team, \
    update_mp_team

stripe.api_key = os.getenv('STRIPE_SK')

PERMISSION_COMMON = {
    'can_add', 'can_list', 'can_show', 'can_edit', 'can_invitation', 'can_invitation_post'
}

NOT_ALLOWED_SQL_PERM = {
    'can_sql_json', 'can_csv', 'can_search_queries', 'can_sqllab_viz',
    'can_sqllab',
}

OWNER_NOT_ALLOWED_MENU = {
    'List Users', 'List Roles', 'Base Permissions', 'Views/Menus',
    'Permission on Views/Menus', 'Action Log',
    'Manage', 'Druid Clusters', 'Druid Datasources',
    'Scan New Datasources', 'Refresh Druid Metadata',
    'SQL Lab',
}

# OWNER_PERMISSION_MODEL = {
#     'UserDBModelView',
#     'DatabaseView',
#     'SliceModelView',
#     'SliceAddView',
#     'TableModelView',
#     # 'DashboardModelView',
#     # 'DashboardAddView',
#     'SolarBIModelAddView',
#     'SolarBIModelWelcomeView',
#     'SolarBIModelView',
#     'SolarBIRegisterInvitationUserDBView',
#     'SolarBIRegisterUserModelView',
#     'SolarBIUserStatsChartView',
#     'SolarBIUserInfoEditView',
#     'SolarBIResetMyPasswordView',
# }

# OWNER_NOT_ALLOWED_PERM_MENU = {
#     'SavvySiteModelView': ['can_add', 'can_delete'],
#     'UserDBModelView': ['can_list', 'can_add', 'can_edit', 'can_delete'],
#     'RegisterUserModelView': ['can_list'],
#     'LogModelView': ['can_list', 'can_download', 'can_edit', 'can_show', 'can_delete', 'can_add'],
#     'RoleModelView': ['can_list', 'can_download', 'can_edit', 'can_show', 'can_delete', 'can_add'],
#     'DashboardModelView': ['can_list', 'can_download', 'can_edit', 'can_show', 'can_delete', 'can_add'],
# }

OWNER_PERMISSION_MENU = {
    'SolarBI', 'Search your Location', 'Saved Solar Data', 'Introduction'
}

OWNER_INVITE_ROLES = {
    'solar_default',
}

OWNER_PERMISSIONS_VIEWS = [
    ('can_explore_json', 'Superset'),
    ('resetmypassword', 'UserDBModelView'),
    ('can_this_form_post', 'ResetMyPasswordView'),
    ('can_this_form_get', 'ResetMyPasswordView'),
    ('can_this_form_post', 'UserInfoEditView'),
    ('can_this_form_get', 'UserInfoEditView'),
    ('can_this_form_post', 'SolarBIUserInfoEditView'),
    ('can_this_form_get', 'SolarBIUserInfoEditView'),
    ('can_this_form_post', 'SolarBIResetMyPasswordView'),
    ('can_this_form_get', 'SolarBIResetMyPasswordView'),
    # ('can_userinfo', 'UserDBModelView'),
    ('userinfoedit', 'UserDBModelView'),
    ('can_invitation', 'SolarBIRegisterInvitationUserDBView'),
    ('can_invitation_post', 'SolarBIRegisterInvitationUserDBView'),
    ('can_billing', 'SolarBIBillingView'),
    ('can_dashboard', 'SolarBIModelView'),
    # ('can_mydashboard', 'SolarBIDashboardView'),
]
OWNER_PERMISSIONS_COMMON = ['can_show', 'can_list', 'can_delete', 'can_add']
OWNER_PERMISSIONS_VIEW = ['SolarBIModelAddView', 'SolarBIModelWelcomeView',
                          'SolarBIModelView', 'SolarBIBillingView']

# SUPERUSER_INVITE_ROLES = {
#     'org_user', 'org_viewer',
# }

# USER_NOT_ALLOWED = {
#     'Druid Clusters', 'Druid Datasources', 'Scan New Datasources', 'SavvyRegisterInvitationUserDBView',
#     'SavvyGroupModelView', 'List Group', 'SavvySiteModelView',
# }

# VIEWER_NOT_ALLOWED = {
#     'Sources',
# }

DB_ROLE_PREFIX = 'team_db_'


class CustomSecurityManager(SupersetSecurityManager):
    passwordrecoverview = SolarBIPasswordRecoverView()
    passwordresetview = SolarBIResetPasswordView()
    invite_register_view = SolarBIRegisterInvitationView()
    invitation_view = SolarBIRegisterInvitationUserDBView()

    credit_register_view = SolarBICreditRegisterView()
    trial_register_view = SolarBITrialRegisterView()

    registeruserdbview = SolarBIRegisterUserDBView
    authdbview = SolarBIAuthDBView
    registeruser_model = TeamRegisterUser
    # userdbmodelview = SolarBIUserDBModelView
    userinfoeditview = SolarBIUserInfoEditView
    resetmypasswordview = SolarBIResetMyPasswordView

    resetRequest_model = ResetRequest
    team_model = Team
    user_model = SolarBIUser
    team_role = TeamRole

    subscription_model = TeamSubscription

    def __init__(self, appbuilder):
        super(CustomSecurityManager, self).__init__(appbuilder)

    def register_views(self):
        super(CustomSecurityManager, self).register_views()
        self.appbuilder.add_view_no_menu(self.passwordrecoverview)
        self.appbuilder.add_view_no_menu(self.passwordresetview)
        self.appbuilder.add_view_no_menu(self.invite_register_view)
        self.appbuilder.add_view_no_menu(self.invitation_view)
        self.appbuilder.add_view_no_menu(self.credit_register_view)
        self.appbuilder.add_view_no_menu(self.trial_register_view)

    def sync_role_definitions(self):
        """Inits the Superset application with security roles and such"""
        from superset import conf
        logging.info('Syncing role definition')

        self.create_custom_permissions()

        # Creating default roles
        self.set_role("Admin", self._is_admin_pvm)
        self.set_role("Alpha", self._is_alpha_pvm)
        self.set_role("Gamma", self._is_gamma_pvm)
        self.set_role("granter", self._is_granter_pvm)
        self.set_role("sql_lab", self._is_sql_lab_pvm)
        self.set_role("solar_default", self.is_solar_pvm)
        self.set_role('team_owner', self.is_owner_pvm)

        if conf.get('PUBLIC_ROLE_LIKE_GAMMA', False):
            self.set_role('Public', self._is_gamma_pvm)

        self.create_missing_perms()
        # commit role and view menu updates
        self.get_session.commit()
        self.clean_perms()

        # create team roles
        self.create_team_roles()

    def _has_view_access(
            self, user: object, permission_name: str, view_name: str
    ) -> bool:

        if user.roles[0].name == 'Admin':
            return True
            
        team_id, team_name = get_session_team(self, user.id)
        team_roles = user.team_role
        db_role_ids = list()

        # First check against builtin (statically configured) roles
        # because no database query is needed
        for team_role in team_roles:
            if team_role.role.name in self.builtin_roles:
                if self._has_access_builtin_roles(
                        team_role.role,
                        permission_name,
                        view_name
                ):
                    return True
            else:
                if str(team_role.team.id) == str(team_id):
                    db_role_ids.append(team_role.role.id)

        # Then check against database-stored roles
        return self.exist_permission_on_roles(
            view_name,
            permission_name,
            db_role_ids,
        )

    def create_team_roles(self):
        logging.info('Create team role for existed teams and users')
        try:
            teams = self.get_session.query(Team).all()
            owner_role = self.find_role('team_owner')
            default_role = self.find_role('solar_default')
            for team in teams:
                logging.info(f'Team {team.team_name}')
                owner_team_role = self.find_team_role(team.id, owner_role.id)
                default_team_role = self.find_team_role(team.id, default_role.id)

                for user in team.users:
                    if user.roles[0].name == 'team_owner' and owner_team_role not in user.team_role:
                        user.team_role.append(owner_team_role)
                    elif user.roles[0].name == 'solar_default' and default_team_role not in user.team_role:
                        user.team_role.append(default_team_role)
                    self.get_session.merge(user)

            self.get_session.commit()
        except Exception as e:
            logging.error(e)
            self.get_session.rollback()

    def is_owner_pvm(self, pvm):
        result = False
        for item in OWNER_PERMISSIONS_VIEWS:
            result = result or (pvm.view_menu.name == item[1] and
                                pvm.permission.name == item[0])
        for permission in OWNER_PERMISSIONS_COMMON:
            for view in OWNER_PERMISSIONS_VIEW:
                result = result or (pvm.view_menu.name == view and
                                    pvm.permission.name == permission)
        # for menu in SOLAR_PERMISSIONS_MENU:
        #     result = result or (pvm.view_menu.name == menu and
        #                         pvm.permission.name == 'menu_access')
        return result

    @property
    def get_url_for_recover(self):
        return url_for('%s.%s' % (self.passwordrecoverview.endpoint,
                                  self.passwordrecoverview.default_view))

    def get_url_for_reset(self, token):
        return url_for('%s.%s' % (self.passwordresetview.endpoint,
                                  self.passwordresetview.default_view), token=token)

    def add_reset_request(self, email):
        """try look for not used existed hash for user"""
        reset_request = self.get_session.query(self.resetRequest_model) \
            .filter_by(email=email, used=False).first()
        if reset_request is not None:
            self.set_token_used(reset_request.reset_hash)
        reset_request = self.resetRequest_model()
        reset_request.email = email
        reset_request.used = False
        user = self.find_user(email=email)

        if user is not None:
            reset_request.user_id = user.id
            hash_token = generate_password_hash(email)
            reset_request.reset_hash = hash_token
            try:
                self.get_session.add(reset_request)
                self.get_session.commit()

                #log to mixpanel
                log_to_mp(user, '', 'request password reset', {})

                return hash_token
            except Exception as e:
                self.appbuilder.get_session.rollback()
        return None

    def get_url_for_invitation(self, token, existed=False):
        if not existed:
            return url_for('%s.%s' % (self.invite_register_view.endpoint,
                                      'invitation'), invitation_hash=token, _external=True)
        else:
            pass

    def find_user_by_token(self, token):
        reset_request = self.get_session.query(self.resetRequest_model)\
            .filter_by(reset_hash=token, used=False).first()
        if reset_request is not None:
            time = reset_request.reset_date
            current_time = datetime.datetime.now()
            time_diff = (current_time - time).total_seconds()
            if time_diff < 3600:
                """Check time diff of reset hash time"""
                email = reset_request.email
                user = self.find_user(email=email)
                return user
        return None

    def set_token_used(self, token):
        reset_request = self.get_session.query(self.resetRequest_model) \
            .filter_by(reset_hash=token).first()
        reset_request.used = True
        try:
            self.get_session.merge(reset_request)
            self.get_session.commit()
        except Exception as e:
            self.get_session.rollback()

    def add_team(self, user, team_name, date=None, credit=None, plan_id=None, trial_days=None):
        new_team = self.team_model()
        new_team.team_name = team_name
        if date:
            new_team.date_created = date
        new_team.users.append(user)

        admin_role = self.find_role('team_owner')
        admin_team_role = self.find_team_role(new_team.id, admin_role.id)


        user_role = self.find_role('solar_default')
        user_team_role = self.find_team_role(new_team.id, user_role.id)

        user.team_role.append(admin_team_role)

        try:
            self.get_session.add(new_team)

            self.get_session.merge(user)
            self.get_session.commit()
            self.create_stripe_user_and_sub(user, new_team, credit, plan_id, trial_days)

            create_mp_team(new_team)
            mp_add_user_to_team(user, new_team)
            log_to_mp(user, new_team.team_name, 'activate new team', {
                'team name': new_team.team_name
            })

            return new_team
        except Exception as e:
            logging.error(const.LOGMSG_ERR_SEC_ADD_REGISTER_USER.format(str(e)))
            self.appbuilder.get_session.rollback()
            return None

    def find_team(self, team_id=None, team_name=None, user_id=None):
        if team_name:
            return self.get_session.query(self.team_model).filter_by(team_name=team_name).order_by(self.team_model.id).first()
        elif user_id:
            user = self.get_session.query(self.user_model).filter_by(id=user_id).first()
            if len(user.team_role) > 0:
                return user.team_role[0].team
            else:
                return None
        elif team_id:
            return self.get_session.query(self.team_model).filter_by(id=team_id).first()

    def get_teams_for_user(self, user_id):
        user = self.get_session.query(self.user_model).filter_by(id=user_id).first()
        teams = []
        for team_role in user.team_role:
            teams.append((team_role.team.id, team_role.team.team_name))
        return teams

    def get_role_in_team(self, user, team_id):
        for team_role in user.team_role:
            if team_role.team.id == team_id:
                return team_role.role
        return None

    def find_team_role(self, team_id, role_id):
        team_role = self.get_session.query(self.team_role).filter_by(team_id=team_id, role_id=role_id).first()
        if team_role is None:
            try:
                team_role = self.team_role()
                team_role.team_id = team_id
                team_role.role_id = role_id
                self.get_session.add(team_role)
                self.get_session.commit()
            except Exception as e:
                logging.error(e)
                self.get_session.rollback()
        return team_role

    '''Called when the new invited user activated its account. Create user in ab_user table and add it to the team.'''
    def add_team_user(self, email, first_name, last_name, username, hashed_password, team, role_id):
        try:
            team = self.find_team(team_name=team)
            user = self.user_model()
            user.email = email
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.active = True
            user.email_confirm = True
            user.password = hashed_password
            role = self.get_session.query(self.role_model).filter_by(id=role_id).first()
            user.roles.append(role)
            if team is not None:
                team.users.append(user)
                user_role = self.get_session.query(TeamRole).filter_by(team_id=team.id, role_id=role.id).first()
                user.team_role.append(user_role)

                update_mp_user(user)
                mp_add_user_to_team(user, team)
                log_to_mp(user, team.team_name, 'added to team', {
                    'role': role.name,
                })

                # db_role = self.find_role(DB_ROLE_PREFIX+team.team_name)
                # user.roles.append(db_role)
            self.get_session.add(user)
            self.get_session.merge(team)
            self.get_session.commit()

            return True
        except Exception as e:
            logging.error(e)
            return False

    def del_register_user_and_user(self, register_user):
        try:
            super(CustomSecurityManager, self).del_register_user(register_user)
            user = self.find_user(username=register_user.username)
            if user:
                self.get_session.delete(user)
                self.get_session.commit()
            return True
        except Exception as e:
            logging.error(str(e))
            self.get_session.rollback()
            return False

    # def delete_team(self, team):
    #     from superset.models.core import Database
    #     from superset.connectors.sqla.models import SqlaTable
    #     try:
    #         self.get_session.delete(team)
    #         database = self.get_session.query(Database).\
    #             filter_by(database_name=team.team_name).first()
    #         if database:
    #             role = self.get_session.query(self.role_model).\
    #                 filter_by(name=DB_ROLE_PREFIX+team.organization_name).first()
    #             tables = self.get_session.query(SqlaTable).\
    #                          filter_by(database_id=database.id).all() or []
    #             for table in tables:
    #                 self.get_session.delete(table)
    #             self.get_session.delete(database)
    #             self.get_session.delete(role)
    #         register = self.get_session.query(self.registeruser_model).\
    #             filter_by(team=team.team_name).all()
    #         if register:
    #             for item in register:
    #                 self.get_session.delete(item)
    #         self.get_session.commit()
    #     except Exception as e:
    #         self.get_session.rollback()

    ''' Used for registering new team and admin'''
    def add_register_user_team_admin(self, **kwargs):
        register_user = self.registeruser_model()
        register_user.first_name = kwargs['first_name']
        register_user.last_name = kwargs['last_name']
        register_user.username = kwargs['username']
        register_user.email = kwargs['email']
        register_user.team = kwargs['team']
        register_user.password = generate_password_hash(kwargs['password'])
        register_user.registration_hash = str(uuid.uuid1())
        try:
            self.get_session.add(register_user)
            self.get_session.commit()

            # Log register to mp
            log_to_mp(register_user, kwargs['team'], 'register new team', {})

            return register_user
        except Exception as e:
            logging.error(const.LOGMSG_ERR_SEC_ADD_REGISTER_USER.format(str(e)))
            self.appbuilder.get_session.rollback()
            return None

    def find_invite_hash(self, invitation_hash):
        try:
            reg_user = self.find_register_user(invitation_hash)
            team_name = reg_user.team

            inviter = self.get_user_by_id(reg_user.inviter)
            inviter = inviter.get_full_name()
            email = reg_user.email
            role = self.get_session.query(self.role_model).filter_by(id=reg_user.role_assigned).first()
            if datetime.datetime.now() > reg_user.valid_date:
                raise Exception("Invitation link expired")
            if reg_user.first_name is not None:
                raise Exception("Invitation link already used")
            return team_name, inviter, email, role.name
        except Exception as e:
            logging.error(e)
            return None, None, None, None

    '''Called when invited user received invitation and changed its detail'''
    def edit_invite_register_user_by_hash(self, invitation_hash, first_name=None, last_name=None, username=None,
                                          password='', hashed_password=''):
        invited_user = self.find_register_user(invitation_hash)
        if first_name:
            invited_user.first_name = first_name
        if last_name:
            invited_user.last_name = last_name
        if username:
            invited_user.username = username
        if hashed_password:
            invited_user.password = hashed_password
        else:
            invited_user.password = generate_password_hash(password)
        try:
            self.get_session.merge(invited_user)
            self.get_session.commit()

            # Create the user in mixpanel
            update_mp_user(invited_user)
            log_to_mp(invited_user, '', 'invited user received and updated', {})

            return invited_user
        except Exception as e:
            self.get_session.rollback()
            logging.error(e)
            return None

    '''Gives the list of roles that is allowed to be invited by the inviter'''
    def find_invite_roles(self, inviter_id):
        inviter = self.get_user_by_id(inviter_id)
        for role in inviter.roles:
            if role.name == 'team_owner':
                invite_roles = [self.find_role(role_name) for role_name in OWNER_INVITE_ROLES]
                return [(str(invite_role.id), invite_role.name) for invite_role in invite_roles]
            elif role.name == 'Admin':
                return [(str(invite_role.id), invite_role.name) for invite_role in self.get_all_roles()]

    def find_solar_default_role_id(self):
        return self.get_session.query(self.role_model).filter_by(name='solar_default').first()

    def get_awaiting_emails(self, team):
        all_waiting_users = self.get_session.query(self.registeruser_model).filter_by(team=team.team_name).all()
        return self.invitation_is_valid(all_waiting_users)

    def get_registered_user(self, user_email):
        reg_user = self.get_session.query(self.registeruser_model).filter_by(email=user_email).first()
        return reg_user

    def get_team_members(self, team_id):
        team = self.find_team(team_id=team_id)
        email_role = []
        team_users = sorted(team.users, key=lambda x: x.id)
        for user in team_users:
            for user_role in user.team_role:
                if user_role.team.id == team.id:
                    if user_role.role.name == 'team_owner':
                        email_role.append((user.email, 'Admin'))
                    elif user_role.role.name == 'solar_default':
                        email_role.append((user.email, 'User'))
        return email_role

    def get_new_team_users_count(self, team_id):
        team = self.find_team(team_id=team_id)
        one_week_early = datetime.datetime.now() - datetime.timedelta(days=7)
        new_team_users = [user for user in team.users if user.created_on >= one_week_early]
        return len(new_team_users)

    def get_session_team(self, user_id):
        team = self.get_session.query(Team).filter_by(id=get_session_team(self, user_id)[0]).first()
        return team

    def update_team_name(self, user_id, new_team_name):
        # current_team_name = self.find_team(user_id=user_id).team_name
        current_team_name = self.get_session_team(user_id).team_name
        awaiting_users = self.get_session.query(self.registeruser_model).filter_by(
            team=current_team_name).all()
        for user in awaiting_users:
            user.team = new_team_name

        team = self.get_session.query(self.team_model).filter_by(team_name=current_team_name).first()
        team.team_name = new_team_name
        set_session_team(team.id, team.team_name)
        self.get_session.commit()
        return True

    def invitation_is_valid(self, users):
        user_valid = []
        for user in users:
            if datetime.datetime.now() > user.valid_date:
                user_valid.append((user.email, False))
            else:
                user_valid.append((user.email, True))

        return user_valid

    '''Called when the team admin creates invitation for the email.'''
    def add_invite_register_user(self, email, team, first_name=None, last_name=None,
                                 role=None, inviter=None, password='', hashed_password=''):
        invited_user = self.find_user(email=email)
        existed = invited_user is not None
        if not existed:
            # Invite new user to the system
            invited_user = self.registeruser_model()
            # email and team parameters should be always available.
            invited_user.email = email
            invited_user.team = team.team_name
            invited_user.username = 'solarbi_' + \
                ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=8))

            if first_name:
                invited_user.first_name = first_name
            if last_name:
                invited_user.last_name = last_name
            if inviter:
                invited_user.inviter = inviter
            if role:
                invited_user.role_assigned = role
            if hashed_password:
                invited_user.password = hashed_password
            else:
                invited_user.password = generate_password_hash(password)

                invited_user.registration_hash = str(uuid.uuid1())
                try:
                    self.get_session.add(invited_user)
                    self.get_session.commit()

                except Exception as e:
                    self.get_session.rollback()
                    logging.error(e)
                    raise ValueError('Invitation is failed because of database integrity error')
        else:
            # add existed user to the team
            user_role = self.get_session.query(TeamRole).filter_by(team_id=team.id, role_id=role).first()
            invited_user.team_role.append(user_role)
            team.users.append(invited_user)


            try:
                self.get_session.merge(invited_user)
                self.get_session.merge(team)
                self.get_session.commit()
            except Exception as e:
                self.get_session.rollback()
                logging.error(e)
                raise ValueError('Invitation is failed because of database integrity error')

        # Log to mixpanel
        inviter = self.get_session.query(self.user_model).filter_by(id=inviter).first()
        log_to_mp(inviter, team.team_name, 'create invitation', {
            'invited email': email
        })

        return invited_user, existed

    def delete_invited_user(self, user_email):
        try:
            user = self.get_session.query(self.registeruser_model).\
                filter_by(email=user_email).first()
            self.del_register_user(user)
            return True
        except Exception:
            self.get_session.rollback()
            return False

    def auth_solarbi_user_db(self, username, password):
        """
            Method for authenticating SolarBI user, auth db style

            :param username:
                The username or registered email address
            :param password:
                The password, will be tested against hashed password on db
        """
        if username is None or username == "":
            return None
        user = self.find_user(username=username)
        if user is None:
            user = self.find_user(email=username)
        if user is None or (not user.is_active):
            # log.info(LOGMSG_WAR_SEC_LOGIN_FAILED.format(username))
            return None
        elif check_password_hash(user.password, password):
            self.update_user_auth_stat(user, True)
            return user
        else:
            self.update_user_auth_stat(user, False)
            # log.info(LOGMSG_WAR_SEC_LOGIN_FAILED.format(username))
            return None

    def create_stripe_user_and_sub(self, user, team, credit=None, plan_id=None, trial_days=None, recover=False):
        try:
            resp = stripe.Customer.create(email=user.email, name=f'{user.first_name} {user.last_name}',
                                          description=team.team_name)
            team.stripe_user_id = resp['id']
            if credit:
                resp = stripe.Customer.create_balance_transaction(
                    resp['id'],
                    amount=credit * -1,
                    currency='aud'
                )
            logging.info(resp)

            # add subscription to free tier
            if plan_id:
                user.trial_used = True
                plan = self.get_session.query(Plan).filter_by(id=plan_id).first()
            else:
                plan = self.get_session.query(Plan).filter_by(id=1).first()
            if trial_days:
                utc_trial_end_ts = datetime.datetime.now().timestamp()
            sub_resp = stripe.Subscription.create(customer=team.stripe_user_id, trial_end=int(utc_trial_end_ts)+14*24*3600 if trial_days else None,
                                                  items=[{
                'plan': plan.stripe_id,
                'quantity': '1'
            }])
            # team_subscription.trial_used = True
            if not recover:
                team_subscription = self.subscription_model()
                team_subscription.team = team.id
                team_subscription.plan = plan.id
                team_subscription.stripe_sub_id = sub_resp['id']
                team_subscription.remain_count = plan.num_request
                user.trial_used = True if trial_days else user.trial_used
                self.get_session.add(team_subscription)
            else:
                old_sub = self.get_subscription(team_id=team.id)
                old_sub.plan = plan.id
                old_sub.remain_count = 0
                old_sub.stripe_sub_id = sub_resp['id']
                old_sub.end_time = None

            self.get_session.merge(user)
            self.get_session.commit()

            return True
        except Exception as e:
            self.get_session.rollback()
            logging.error(e)
            return False

    def get_subscription(self, team_id=None, sub_id=None):
        if team_id:
            subscription = self.get_session.query(TeamSubscription).filter(TeamSubscription.team==team_id).first()
            return subscription
        elif sub_id:
            subscription = self.get_session.query(TeamSubscription).filter(TeamSubscription.stripe_sub_id == sub_id).first()
            return subscription
        else:
            return None

    def find_team_admin(self, team_id=None):
        role = self.find_role('team_owner')
        team_role = self.get_session.query(TeamRole).filter_by(team_id=team_id, role_id=role.id).first()
        admin = team_role.user
        return admin

    def convert_test_user_to_live(self, team):
        user = self.find_team_admin(team_id=team.id)
        try:
            _ = stripe.Customer.retrieve(team.stripe_user_id)
        except stripe.error.InvalidRequestError as e:
            stripe.api_key = "sk_test_lmhjMQ9t1nqu2FNGgR5hv3N600QYlekFDt"
            cus_obj = stripe.Customer.retrieve(team.stripe_user_id)
            stripe.api_key = os.getenv('STRIPE_SK')
            if cus_obj['balance'] != 0:
                self.create_stripe_user_and_sub(user[0], team, credit=-cus_obj['balance'], plan_id=1, recover=True)
            else:
                self.create_stripe_user_and_sub(user[0], team, plan_id=1, recover=True)
