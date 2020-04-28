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
from contextlib import closing
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import logging
import re
import time
import itertools
import requests
import boto3
from typing import Dict, List  # noqa: F401
from urllib import parse
import stripe

from flask import (
    abort,
    flash,
    g,
    Markup,
    redirect,
    render_template,
    request,
    Response,
    url_for,
    session,
)
from flask_appbuilder import expose
from flask_appbuilder.actions import action
from flask_appbuilder.urltools import get_order_args, get_page_args, get_page_size_args, get_filter_args
from flask_appbuilder.models.sqla.filters import FilterEqual, \
    FilterEqualFunction, FilterNotEqual
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import has_access, has_access_api
from flask_appbuilder.security.sqla import models as ab_models
from flask_appbuilder.views import ModelView
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
import pandas as pd
import simplejson as json
from sqlalchemy import and_, or_, select
from werkzeug.routing import BaseConverter
from ..solar.forms import SolarBIListWidget, SolarBIDashboardListWidget, SolarBIProfileWidget
from ..solar.models import Plan, TeamSubscription, Team, StripeEvent
from ..solar.utils import set_session_team, get_session_team, log_to_mp, get_athena_query, send_sendgrid_email
from superset import (
    app,
    appbuilder,
    cache,
    conf,
    db,
    event_logger,
    get_feature_flags,
    is_feature_enabled,
    results_backend,
    security_manager,
    sql_lab,
    viz,
)
from superset.connectors.connector_registry import ConnectorRegistry
from superset.connectors.sqla.models import AnnotationDatasource
from superset.exceptions import (
    DatabaseNotFound,
    SupersetException,
    SupersetSecurityException,
)
from superset.jinja_context import get_template_processor
from superset.legacy import update_time_range
import superset.models.core as models
from superset.models.sql_lab import Query
from superset.models.user_attributes import UserAttribute
from superset.sql_parse import ParsedQuery
from superset.sql_validators import get_validator_by_name
from superset.utils import core as utils
from superset.utils import dashboard_import_export
from superset.utils.dates import now_as_float
from superset.utils.decorators import etag_cache
from .base import (
    api,
    BaseSupersetView,
    check_ownership,
    CsvResponse,
    data_payload_response,
    DeleteMixin,
    generate_download_headers,
    get_error_msg,
    get_user_roles,
    handle_api_exception,
    json_error_response,
    json_success,
    SupersetFilter,
    SupersetModelView,
)
from .utils import (
    apply_display_max_row_limit,
    bootstrap_user_data,
    get_datasource_info,
    get_form_data,
    get_viz,
    format_datetime,
    list_object_key,
    get_user_teams,
)

config = app.config
CACHE_DEFAULT_TIMEOUT = config.get("CACHE_DEFAULT_TIMEOUT", 0)
stats_logger = config.get("STATS_LOGGER")
DAR = models.DatasourceAccessRequest
QueryStatus = utils.QueryStatus

ALL_DATASOURCE_ACCESS_ERR = __(
    "This endpoint requires the `all_datasource_access` permission"
)
DATASOURCE_MISSING_ERR = __("The data source seems to have been deleted")
ACCESS_REQUEST_MISSING_ERR = __("The access requests seem to have been deleted")
USER_MISSING_ERR = __("The user seems to have been deleted")

stripe.api_key = os.getenv('STRIPE_SK')

FORM_DATA_KEY_BLACKLIST: List[str] = []
if not config.get("ENABLE_JAVASCRIPT_CONTROLS"):
    FORM_DATA_KEY_BLACKLIST = ["js_tooltip", "js_onclick_href", "js_data_mutator"]


def get_database_access_error_msg(database_name):
    return __(
        "This view requires the database %(name)s or "
        "`all_datasource_access` permission",
        name=database_name,
    )


def is_owner(obj, user):
    """ Check if user is owner of the slice """
    return obj and user in obj.owners


def check_datasource_perms(
    self, datasource_type: str = None, datasource_id: int = None
) -> None:
    """
    Check if user can access a cached response from explore_json.

    This function takes `self` since it must have the same signature as the
    the decorated method.

    :param datasource_type: The datasource type, i.e., 'druid' or 'table'
    :param datasource_id: The datasource ID
    :raises SupersetSecurityException: If the user cannot access the resource
    """

    form_data = get_form_data()[0]

    try:
        datasource_id, datasource_type = get_datasource_info(
            datasource_id, datasource_type, form_data
        )
    except SupersetException as e:
        raise SupersetSecurityException(str(e))

    viz_obj = get_viz(
        datasource_type=datasource_type,
        datasource_id=datasource_id,
        form_data=form_data,
        force=False,
    )

    security_manager.assert_datasource_permission(viz_obj.datasource)


def check_slice_perms(self, slice_id):
    """
    Check if user can access a cached response from slice_json.

    This function takes `self` since it must have the same signature as the
    the decorated method.

    """
    form_data, slc = get_form_data(slice_id, use_slice_data=True)
    datasource_type = slc.datasource.type
    datasource_id = slc.datasource.id
    viz_obj = get_viz(
        datasource_type=datasource_type,
        datasource_id=datasource_id,
        form_data=form_data,
        force=False,
    )
    security_manager.assert_datasource_permission(viz_obj.datasource)


class SliceFilter(SupersetFilter):
    def apply(self, query, func):  # noqa
        if security_manager.all_datasource_access():
            return query
        perms = self.get_view_menus("datasource_access")
        # TODO(bogdan): add `schema_access` support here
        return query.filter(self.model.perm.in_(perms))


class DashboardFilter(SupersetFilter):
    """
    List dashboards with the following criteria:
        1. Those which the user owns
        2. Those which the user has favorited
        3. Those which have been published (if they have access to at least one slice)

    If the user is an admin show them all dashboards.
    This means they do not get curation but can still sort by "published"
    if they wish to see those dashboards which are published first
    """

    def apply(self, query, func):  # noqa
        Dash = models.Dashboard
        User = ab_models.User
        Slice = models.Slice  # noqa
        Favorites = models.FavStar

        user_roles = [role.name.lower() for role in list(self.get_user_roles())]
        if "admin" in user_roles:
            return query

        datasource_perms = self.get_view_menus("datasource_access")
        all_datasource_access = security_manager.all_datasource_access()
        published_dash_query = (
            db.session.query(Dash.id)
            .join(Dash.slices)
            .filter(
                and_(
                    Dash.published == True,  # noqa
                    or_(Slice.perm.in_(datasource_perms), all_datasource_access),
                )
            )
        )

        users_favorite_dash_query = db.session.query(Favorites.obj_id).filter(
            and_(
                Favorites.user_id == User.get_user_id(),
                Favorites.class_name == "Dashboard",
            )
        )
        owner_ids_query = (
            db.session.query(Dash.id)
            .join(Dash.owners)
            .filter(User.id == User.get_user_id())
        )

        query = query.filter(
            or_(
                Dash.id.in_(owner_ids_query),
                Dash.id.in_(published_dash_query),
                Dash.id.in_(users_favorite_dash_query),
            )
        )

        return query


from .database import api as database_api  # noqa
from .database import views as in_views  # noqa

if config.get('ENABLE_ACCESS_REQUEST'):
    class AccessRequestsModelView(SupersetModelView, DeleteMixin):
        datamodel = SQLAInterface(DAR)
        list_columns = [
            "username",
            "user_roles",
            "datasource_link",
            "roles_with_datasource",
            "created_on",
        ]
        order_columns = ["created_on"]
        base_order = ("changed_on", "desc")
        label_columns = {
            "username": _("User"),
            "user_roles": _("User Roles"),
            "database": _("Database URL"),
            "datasource_link": _("Datasource"),
            "roles_with_datasource": _("Roles to grant"),
            "created_on": _("Created On"),
        }

    appbuilder.add_view(
        AccessRequestsModelView,
        "Access requests",
        label=__("Access requests"),
        category="Security",
        category_label=__("Security"),
        icon="fa-table",
    )


class SliceModelView(SupersetModelView, DeleteMixin):  # noqa
    route_base = "/chart"
    datamodel = SQLAInterface(models.Slice)

    list_title = _("Charts")
    show_title = _("Show Chart")
    add_title = _("Add Chart")
    edit_title = _("Edit Chart")

    can_add = False
    search_columns = (
        "slice_name",
        "description",
        "viz_type",
        "datasource_name",
        "owners",
    )
    list_columns = ["slice_link", "viz_type", "datasource_link", "creator", "modified"]
    order_columns = ["viz_type", "datasource_link", "modified"]
    edit_columns = [
        "slice_name",
        "description",
        "viz_type",
        "owners",
        "dashboards",
        "params",
        "cache_timeout",
    ]
    base_order = ("changed_on", "desc")
    description_columns = {
        "description": Markup(
            "The content here can be displayed as widget headers in the "
            "dashboard view. Supports "
            '<a href="https://daringfireball.net/projects/markdown/"">'
            "markdown</a>"
        ),
        "params": _(
            "These parameters are generated dynamically when clicking "
            "the save or overwrite button in the explore view. This JSON "
            "object is exposed here for reference and for power users who may "
            "want to alter specific parameters."
        ),
        "cache_timeout": _(
            "Duration (in seconds) of the caching timeout for this chart. "
            "Note this defaults to the datasource/table timeout if undefined."
        ),
    }
    base_filters = [['id', SliceFilter, lambda: []],
                    ['viz_type', FilterNotEqual, 'solarBI']]
    label_columns = {
        "cache_timeout": _("Cache Timeout"),
        "creator": _("Creator"),
        "dashboards": _("Dashboards"),
        "datasource_link": _("Datasource"),
        "description": _("Description"),
        "modified": _("Last Modified"),
        "owners": _("Owners"),
        "params": _("Parameters"),
        "slice_link": _("Chart"),
        "slice_name": _("Name"),
        "table": _("Table"),
        "viz_type": _("Visualization Type"),
    }

    add_form_query_rel_fields = {"dashboards": [["name", DashboardFilter, None]]}

    edit_form_query_rel_fields = add_form_query_rel_fields

    def pre_add(self, obj):
        utils.validate_json(obj.params)

    def pre_update(self, obj):
        utils.validate_json(obj.params)
        check_ownership(obj)

    def pre_delete(self, obj):
        check_ownership(obj)

    @expose("/add", methods=["GET", "POST"])
    @has_access
    def add(self):
        datasources = ConnectorRegistry.get_all_datasources(db.session)
        datasources = [
            {"value": str(d.id) + "__" + d.type, "label": repr(d)} for d in datasources
        ]
        return self.render_template(
            "superset/add_slice.html",
            bootstrap_data=json.dumps(
                {"datasources": sorted(datasources, key=lambda d: d["label"])}
            ),
        )


appbuilder.add_view(
    SliceModelView,
    "Charts",
    label=__("Charts"),
    icon="fa-bar-chart",
    category="",
    category_icon="",
)


def get_user():
    return g.user


def get_team_id():
    return session['team_id']


# class SolarBIModelView(SliceModelView):  # noqa
#     pass


# class SolarBIModelWelcomeView(SolarBIModelView):
#     pass


class SolarBIModelView(SupersetModelView, DeleteMixin):
    route_base = '/solar'
    # datamodel = SQLAInterface(models.Slice)
    datamodel = SQLAInterface(models.SolarBISlice)
    base_filters = [['viz_type', FilterEqual, 'solarBI'],
                    ['team_id', FilterEqualFunction, get_team_id]]
                    # ['created_by', FilterEqualFunction, get_user]]
    base_permissions = ['can_list', 'can_show', 'can_add', 'can_delete', 'can_edit',
                        'can_dashboard', 'can_profile']

    search_columns = (
        'slice_name', 'description', 'owners',
    )
    list_columns = [
        'slice_link', 'creator', 'modified', 'view_slice_name', 'view_slice_link', 'slice_query_id',
        'slice_download_link', 'slice_id', 'changed_by_name'
    ]
    edit_columns = [
        "slice_name",
        "description",
        "viz_type",
        "owners",
        "params",
        "cache_timeout",
    ]

    order_columns = ['modified']

    filters_not_for_admin = {}

    list_template = 'solar/my_data_list.html',
    list_title = 'My Data - SolarBI'
    list_widget = SolarBIListWidget

    dashboard_template = 'solar/my_dashboard.html',
    dashboard_title = 'My Dashboard - SolarBI'
    dashboard_widget = SolarBIDashboardListWidget

    profile_template = 'solar/my_profile.html',
    profile_title = 'My Profile -SolarBI'
    profile_widget = SolarBIProfileWidget

    @expose('/dashboard')
    @has_access
    def dashboard(self):

        for team_role in g.user.team_role:
            role = team_role.role
            if role.name == 'Admin':
                self.remove_filters_for_role(role.name)
                break
            else:
                self.add_filters_for_role(role.name)
        widgets = self._dashboard()
        return self.render_template(self.dashboard_template,
                                    title=self.dashboard_title,
                                    widgets=widgets)

    def _dashboard(self):
        if get_order_args().get(self.__class__.__name__):
            order_column, order_direction = get_order_args().get(
                self.__class__.__name__
            )
        else:
            order_column, order_direction = "", ""
        page = get_page_args().get(self.__class__.__name__)
        page_size = get_page_size_args().get(self.__class__.__name__)
        get_filter_args(self._filters)
        widgets = self._get_dashboard_widget(
            filters=self._filters,
            order_column=order_column,
            order_direction=order_direction,
            page=page,
            page_size=page_size,
        )
        form = self.search_form.refresh()
        self.update_redirect()
        return self._get_search_widget(form=form, widgets=widgets)

    def _get_dashboard_widget(
            self,
            filters,
            actions=None,
            order_column="",
            order_direction="",
            page=None,
            page_size=None,
            widgets=None,
            **args
    ):
        """ get joined base filter and current active filter for query """
        # pylint: disable=unpacking-non-sequence
        widgets = widgets or {}
        actions = actions or self.actions
        page_size = page_size or self.page_size
        if not order_column and self.base_order:
            order_column, order_direction = self.base_order
        joined_filters = filters.get_joined_filters(self._base_filters)
        count, lst = self.datamodel.query(
            joined_filters,
            order_column,
            order_direction,
            page=page,
            page_size=page_size,
        )
        pks = self.datamodel.get_keys(lst)

        # serialize composite pks
        pks = [self._serialize_pk_if_composite(pk) for pk in pks]

        all_object_keys = []
        try:
            all_object_keys = list_object_key('colin-query-test',
                                                'TID' + str(get_session_team(
                                                       self.appbuilder.sm, g.user.id)[
                                                                   0]) + '/')
        except Exception:
            pass

        obj_keys = []
        avail_object_keys = []
        if all_object_keys:
            avail_object_keys = [key for key in all_object_keys if key.endswith('.csv')]
            obj_keys = [key.split('/')[2].replace('.csv', '') for key in
                        avail_object_keys]

        # Get current session team
        session_team = get_session_team(self.appbuilder.sm, g.user.id)

        # Get remaining advance requests in this billing period
        subscription = self.appbuilder.sm.get_subscription(team_id=session_team[0])
        remain_advanced_searches = subscription.remain_count
        # Get the total number of advance requests in the history
        value_generator = self.datamodel.get_values(lst, self.list_columns)
        history_advance_count = len([item['slice_query_id'] for item in value_generator
                                    if item['slice_query_id'] != 'None'])
        # Get the number of team members
        cur_team = self.appbuilder.sm.find_team(team_id=session_team[0])
        awaiting_emails = self.appbuilder.sm.get_awaiting_emails(cur_team)
        team_users = self.appbuilder.sm.get_team_members(cur_team.id)
        team_users_count = len(cur_team.users)
        # Get the number of new team members who joined in this week
        new_team_users_count = self.appbuilder.sm.get_new_team_users_count(session_team[0])
        # Get the current plan name
        plan_name = self.appbuilder.get_session.query(Plan).filter_by(id=subscription.plan).first().plan_name

        widgets["dashboard"] = self.dashboard_widget(
            appbuilder=self.appbuilder,
            session_team=session_team,
            avail_object_keys=avail_object_keys,
            obj_keys=obj_keys,
            remain_advanced_searches=remain_advanced_searches,
            history_advance_count=history_advance_count,
            team_users_count=team_users_count,
            new_team_users_count=new_team_users_count,
            plan_name=plan_name,
            format_datetime=format_datetime,
            awaiting_emails=awaiting_emails,
            team_users=team_users,
            label_columns=self.label_columns,
            include_columns=self.list_columns,
            value_columns=itertools.islice(self.datamodel.get_values(lst, self.list_columns), 5),
            order_columns=self.order_columns,
            formatters_columns=self.formatters_columns,
            page=page,
            page_size=page_size,
            count=count,
            pks=pks,
            actions=actions,
            filters=filters,
            modelview_name=self.__class__.__name__,
        )
        return widgets

    @expose('/profile')
    @has_access
    def profile(self):

        for team_role in g.user.team_role:
            role = team_role.role
            if role.name == 'Admin':
                self.remove_filters_for_role(role.name)
                break
            else:
                self.add_filters_for_role(role.name)
        widgets = self._profile()
        return self.render_template(self.profile_template,
                                    title=self.profile_title,
                                    widgets=widgets)

    def _profile(self):
        if get_order_args().get(self.__class__.__name__):
            order_column, order_direction = get_order_args().get(
                self.__class__.__name__
            )
        else:
            order_column, order_direction = "", ""
        page = get_page_args().get(self.__class__.__name__)
        page_size = get_page_size_args().get(self.__class__.__name__)
        get_filter_args(self._filters)
        widgets = self._get_profile_widget(
            filters=self._filters,
            order_column=order_column,
            order_direction=order_direction,
            page=page,
            page_size=page_size,
        )
        form = self.search_form.refresh()
        self.update_redirect()
        return self._get_search_widget(form=form, widgets=widgets)

    def _get_profile_widget(
            self,
            filters,
            actions=None,
            order_column="",
            order_direction="",
            page=None,
            page_size=None,
            widgets=None,
            **args
    ):
        """ get joined base filter and current active filter for query """
        # pylint: disable=unpacking-non-sequence
        widgets = widgets or {}
        actions = actions or self.actions
        page_size = page_size or self.page_size
        if not order_column and self.base_order:
            order_column, order_direction = self.base_order
        joined_filters = filters.get_joined_filters(self._base_filters)
        count, lst = self.datamodel.query(
            joined_filters,
            order_column,
            order_direction,
            page=page,
            page_size=page_size,
        )
        pks = self.datamodel.get_keys(lst)

        # serialize composite pks
        pks = [self._serialize_pk_if_composite(pk) for pk in pks]

        # Get current session team
        session_team = get_session_team(self.appbuilder.sm, g.user.id)

        # Get remaining advance requests in this billing period
        subscription = self.appbuilder.sm.get_subscription(team_id=session_team[0])

        # Get the number of team members
        cur_team = self.appbuilder.sm.find_team(team_id=session_team[0])
        awaiting_emails = self.appbuilder.sm.get_awaiting_emails(cur_team)
        team_users = self.appbuilder.sm.get_team_members(cur_team.id)
        team_users_count = len(cur_team.users)
        # Get current user info
        user_info = self.appbuilder.sm.get_user_by_id(g.user.id)

        widgets["profile"] = self.profile_widget(
            appbuilder=self.appbuilder,
            session_team=session_team,
            user_info=user_info,
            team_users_count=team_users_count,
            format_datetime=format_datetime,
            awaiting_emails=awaiting_emails,
            team_users=team_users,
            label_columns=self.label_columns,
            include_columns=self.list_columns,
            value_columns=itertools.islice(self.datamodel.get_values(lst, self.list_columns), 5),
            order_columns=self.order_columns,
            formatters_columns=self.formatters_columns,
            page=page,
            page_size=page_size,
            count=count,
            pks=pks,
            actions=actions,
            filters=filters,
            modelview_name=self.__class__.__name__,
        )
        return widgets

    @expose('/list')
    @has_access
    def list(self):

        for team_role in g.user.team_role:
            role = team_role.role
            if role.name == 'Admin':
                self.remove_filters_for_role(role.name)
                break
            else:
                self.add_filters_for_role(role.name)
        widgets = self._list()
        return self.render_template(self.list_template,
                                    title=self.list_title,
                                    widgets=widgets)

    def _get_list_widget(
            self,
            filters,
            actions=None,
            order_column="",
            order_direction="",
            page=None,
            page_size=None,
            widgets=None,
            **args
    ):
        """ get joined base filter and current active filter for query """
        # pylint: disable=unpacking-non-sequence
        widgets = widgets or {}
        actions = actions or self.actions
        page_size = page_size or self.page_size
        if not order_column and self.base_order:
            order_column, order_direction = self.base_order
        joined_filters = filters.get_joined_filters(self._base_filters)
        count, lst = self.datamodel.query(
            joined_filters,
            order_column,
            order_direction,
            page=page,
            page_size=page_size,
        )
        pks = self.datamodel.get_keys(lst)

        # serialize composite pks
        pks = [self._serialize_pk_if_composite(pk) for pk in pks]

        # team_id = get_team_id()
        # # get all object keys in s3 under all team users' sub folders
        # team_members_email_role = appbuilder.sm.get_team_members(team_id)
        # team_member_emails = []
        # for email, _ in team_members_email_role:
        #     team_member_emails.append(email)

        # all_object_keys = []
        # for me in team_member_emails:
        #     try:
        #         all_object_keys += self.list_object_key('', me + '/')
        #     except Exception:
        #         continue
        all_object_keys = []
        try:
            all_object_keys = list_object_key('colin-query-test',
                                                   'TID' + str(get_session_team(self.appbuilder.sm, g.user.id)[0]) + '/')
        except Exception:
            pass

        obj_keys = []
        avail_object_keys = []
        if all_object_keys:
            avail_object_keys = [key for key in all_object_keys if key.endswith('.csv')]
            obj_keys = [key.split('/')[2].replace('.csv', '') for key in avail_object_keys]

        widgets["list"] = self.list_widget(
            appbuilder=self.appbuilder,
            session_team=get_session_team(self.appbuilder.sm, g.user.id),
            avail_object_keys=avail_object_keys,
            obj_keys=obj_keys,
            label_columns=self.label_columns,
            include_columns=self.list_columns,
            value_columns=self.datamodel.get_values(lst, self.list_columns),
            order_columns=self.order_columns,
            formatters_columns=self.formatters_columns,
            page=page,
            page_size=page_size,
            count=count,
            pks=pks,
            actions=actions,
            filters=filters,
            modelview_name=self.__class__.__name__,
        )
        return widgets

    def remove_filters_for_role(self, role_name):
        if role_name == 'Admin':
            self.remove_filter('created_by')

    def add_filters_for_role(self, role_name):
        if role_name != 'Admin':
            self.add_filters('created_by')

    def add_filters(self, filter_name):
        for f in self.filters_not_for_admin:
            if f.column_name == filter_name:
                self._base_filters.filters.append(f)
                self._base_filters.values.append(self.filters_not_for_admin[f])
                del self.filters_not_for_admin[f]
                break

    def remove_filter(self, filter_name):
        for f in self._base_filters.filters:
            if f.column_name == filter_name:
                index_filter = self._base_filters.filters.index(f)
                value = self._base_filters.values[index_filter]
                self.filters_not_for_admin[f] = value
                self._base_filters.filters.remove(f)
                self._base_filters.values.remove(value)

    @expose('/add', methods=['GET', 'POST'])
    @has_access
    def add(self):
        if not g.user or not g.user.get_id():
            return redirect(appbuilder.get_url_for_login)
        team = self.appbuilder.get_session.query(Team).filter_by(id=session['team_id']).first()
        subscription = self.appbuilder.sm.get_subscription(team_id=team.id)

        self.appbuilder.sm.convert_test_user_to_live(team)
        # Count the subscription remaining days
        # TODO: change default not to -1 in case bug
        remain_days = -1
        if subscription.end_time:
            current_datetime = datetime.utcnow()
            end_datetime = datetime.utcfromtimestamp(subscription.end_time)
            remain_days = (end_datetime - current_datetime).days

            # If has passed 14 days of end time, revert customer plan to free
            if remain_days <= -14:
                self.revert_to_free(team)

                # Remove credit card to force update cc for next time
                team.stripe_pm_id = None

        # Get the saved queries
        _, lst = self.datamodel.query(
            self._filters.get_joined_filters(self._base_filters),
            "",
            "",
            page=None,
            page_size=10,
        )
        saved_queries = [{
            'name': i.data['slice_name'],
            'address': i.data['form_data']['spatial_address']['address'],
            'updateDate': i.changed_on.strftime("%m/%d/%Y"),
            'slice_url': i.slice_url,
        } for i in lst if i.query_id is None]

        entry_point = 'solarBI'

        datasource_id = self.get_solar_datasource()
        is_team_admin = False
        for team_role in g.user.team_role:
            if team_role.team.id == team.id and team_role.role.name == 'team_owner':
                is_team_admin = True
        can_trial = is_team_admin and not g.user.trial_used
        payload = {
            'user': bootstrap_user_data(g.user),
            'common': BaseSupersetView().common_bootstrap_payload(),
            'datasource_id': datasource_id,
            'datasource_type': 'table',
            'saved_queries': saved_queries,
            'remain_count': subscription.remain_count,
            'plan_id': subscription.plan,
            'remain_days': remain_days,
            'can_trial': can_trial,
        }

        return self.render_template(
            'solar/basic.html',
            entry=entry_point,
            title='Search - SolarBI',
            bootstrap_data=json.dumps(payload, default=utils.json_iso_dttm_ser),
        )

    def get_solar_datasource(self):
        for role in g.user.roles:
            if 'solar' in role.name or 'team_owner' in role.name:
                for permission in role.permissions:
                    if permission.permission.name == 'datasource_access':
                        datasource_id = \
                            permission.view_menu.name.split(':')[1].replace(')', '')
                        return datasource_id

    def revert_to_free(self, team):
        try:
            free_plan = self.appbuilder.get_session.query(Plan).filter_by(id=1).first()
            team_sub = self.appbuilder.sm.get_subscription(team_id=team.id)
            if team_sub is None:
                raise Exception('team subscription not found')
            logging.info('Downgrading stripe plan to free.')
            stripe_sub = stripe.Subscription.create(customer=team.stripe_user_id, items=[{
                'plan': free_plan.stripe_id,
                'quantity': '1',
            }])
            logging.info('Old subscription removed and free subscription created')
            logging.info(stripe_sub)
            team_sub.plan = free_plan.id
            team_sub.end_time = stripe_sub['current_period_end']
            team_sub.remain_count = 0
            team = self.appbuilder.sm.find_team(team_id=team_sub.team)
            log_to_mp(None, team.team_name, 'revert to free after 14 days', {})

            self.appbuilder.get_session.commit()
        except Exception as e:
            self.appbuilder.get_session.rollback()
            logging.warning(e)

    # @expose('/demo')
    # def demo(self):
    #     """Personalized welcome page"""
    #
    #     if not g.user or not g.user.get_id():
    #         return redirect(appbuilder.get_url_for_login)
    #
    #     entry_point = 'solarBI'
    #
    #     datasource_id = self.get_solar_datasource()
    #
    #     payload = {
    #         'user': bootstrap_user_data(g.user),
    #         'common': BaseSupersetView().common_bootstrap_payload(),
    #         'datasource_id': datasource_id,
    #         'datasource_type': 'table',
    #         'entry': 'demo',
    #     }
    #
    #     return self.render_template(
    #         'solar/basic.html',
    #         entry=entry_point,
    #         title='Demo - SolarBI',
    #         bootstrap_data=json.dumps(payload, default=utils.json_iso_dttm_ser),
    #     )

    @expose('/switch_team/<team_id>', methods=['GET'])
    def switch_team(self, team_id):
        if not g.user or not g.user.get_id():
            return redirect(appbuilder.get_url_for_login)

        for team_role in g.user.team_role:
            if str(team_role.team.id) == team_id:
                set_session_team(team_role.team.id, team_role.team.team_name)
                return redirect("/")

        flash('Team Error', 'danger')
        return redirect("/")


appbuilder.add_view(
    SolarBIModelView,
    'Saved Solar Data',
    label=__('Saved'),
    icon='fa-save',
    category='SolarBI',
    category_label=__('SolarBI'),
    category_icon='fa-sun-o',
)


class SolarBIBillingView(ModelView):
    route_base = '/billing'
    datamodel = SQLAInterface(Plan)

    @has_access
    @expose('/my-billing', methods=['GET', 'POST'])
    def billing(self):
        if not g.user or not g.user.get_id():
            return redirect(appbuilder.get_url_for_login)

        team = self.appbuilder.get_session.query(Team).filter_by(id=session['team_id']).first()
        team_sub = self.appbuilder.sm.get_subscription(team_id=team.id)

        user = self.appbuilder.sm.find_team_admin(team_id=team.id)
        # Check remain day of the subscription, if passed 14 days change to free plan
        need_update_cc = team.stripe_pm_id is None
        if team_sub.end_time:
            current_time = datetime.utcnow()
            end_datetime = datetime.utcfromtimestamp(team_sub.end_time)
            remain_days = (current_time - end_datetime).days
            if remain_days >= 14:
                need_update_cc = True
                self.revert_to_free(team)

                # Remove credit card to force update cc for next time
                team.stripe_pm_id = None

        plan = self.appbuilder.get_session.query(Plan).filter_by(id=team_sub.plan).first()
        # Retrieve customer basic information
        self.appbuilder.sm.convert_test_user_to_live(team)
        # try:
        #     cus_obj = stripe.Customer.retrieve(team.stripe_user_id)
        # except stripe.error.InvalidRequestError as e:
        #     stripe.api_key = "sk_test_lmhjMQ9t1nqu2FNGgR5hv3N600QYlekFDt"
        #     cus_obj = stripe.Customer.retrieve(team.stripe_user_id)
        #     stripe.api_key = os.getenv('STRIPE_SK')
        #     if cus_obj['balance'] != 0:
        #         self.appbuilder.sm.create_stripe_user_and_sub(user[0],
        #                                                       team,
        #                                                       credit=-cus_obj['balance'],
        #                                                       plan_id=1, recover=True)
        #     else:
        #         self.appbuilder.sm.create_stripe_user_and_sub(user[0], team, plan_id=1, recover=True)

        cus_obj = stripe.Customer.retrieve(team.stripe_user_id)
        cus_name = cus_obj.name
        cus_email = cus_obj.email
        cus_address = cus_obj.address
        cus_abn = ''
        if cus_obj['tax_ids']['data']:
            cus_abn = cus_obj['tax_ids']['data'][0]['value']

        cus_invoices = stripe.Invoice.list(customer=cus_obj['id'])
        cus_invoices = list({'invoice_id': invoice['id'],
                             'date': datetime.utcfromtimestamp(invoice['created']).strftime("%d/%m/%Y"),
                             'link': invoice['invoice_pdf']} for invoice in cus_invoices)

        card_info = None
        card_has_expired = False
        card_expire_soon = False
        if stripe.PaymentMethod.list(customer=team.stripe_user_id, type='card')['data']:
            card_info = stripe.PaymentMethod.list(customer=team.stripe_user_id, type='card')['data'][0]['card']
            one_month_later = str(date.today() + relativedelta(months=1))[:-3]
            card_expire_date = str(card_info['exp_year']) + '-' + ('0' + str(card_info['exp_month']))[-2:]
            if str(date.today())[:-3] > card_expire_date:
                card_has_expired = True
            elif one_month_later >= card_expire_date:
                card_expire_soon = True

        # need to update cc detail if (no detail or pass-due 14 days) and balance less than $50
        need_update_cc = need_update_cc and cus_obj['balance'] > (-1 * 5000)

        entry_point = 'billing'
        payload = {
            'user': bootstrap_user_data(g.user),
            'common': BaseSupersetView().common_bootstrap_payload(),
            'cus_id': team.stripe_user_id,
            'cus_info': {'cus_name': cus_name, 'cus_email': cus_email, 'cus_address': cus_address, 'cus_abn': cus_abn},
            'pm_id': team.stripe_pm_id,
            'plan_id': plan.stripe_id,
            'invoice_list': cus_invoices,
            'card_has_expired': card_has_expired,
            'card_expire_soon': card_expire_soon,
            'card_info': card_info,
            'balance': cus_obj['balance'],
            'need_update_cc': need_update_cc,
        }

        return self.render_template(
            'solar/basic.html',
            entry=entry_point,
            title='Billing - SolarBI',
            bootstrap_data=json.dumps(payload, default=utils.json_iso_dttm_ser),
        )

    @api
    @handle_api_exception
    @expose('/change_plan/<plan_id>/<update_cc>/', methods=['GET', 'POST'])
    def change_plan(self, plan_id=None, update_cc=False):
        if not g.user or not g.user.get_id():
            return json_error_response('Incorrect call to endpoint')
        team = self.appbuilder.sm.find_team(team_id=session['team_id'])
        logging.info(team.stripe_user_id)

        logging.info('Updating plan for {}'.format(team.team_name))
        try:
            stripe_customer = stripe.Customer.retrieve(id=team.stripe_user_id)

            pm_id = team.stripe_pm_id
            if update_cc == '1':
                form_data = get_form_data()[0]['token']
                # stripe.Customer.modify(stripe_customer.stripe_id, source=form_data['id'])
                pm_id = form_data['id']
                logging.info('Updating credit card')
                self.update_ccard(pm_id, team.id)

            (result, id) = self.update_plan(team.id, plan_id)

            if result:
                return json_success(json.dumps({'msg': 'Change plan success!', 'plan_id': id, 'pm_id': pm_id}))
            else:
                raise Exception('Update plan unsuccessful')
        except Exception as e:
            logging.error(e)
            return json_error_response('Cannot change plan')

    @api
    @handle_api_exception
    @expose('/change_billing_detail/<cus_id>/', methods=['POST'])
    def change_billing_detail(self, cus_id):
        if not g.user or not g.user.get_id():
            return json_error_response('Incorrect call to endpoint')
        form_data = get_form_data()[0]

        # Check if we update the abn or not
        cus_obj = stripe.Customer.retrieve(cus_id)
        if cus_obj['tax_ids']['data']:
            if form_data['abn']:
                if cus_obj['tax_ids']['data'][0]['value'] != form_data['abn']:
                    stripe.Customer.delete_tax_id(cus_id, cus_obj['tax_ids']['data'][0]['id'])
                    stripe.Customer.create_tax_id(cus_id, type="au_abn", value=form_data['abn'])
            else:
                stripe.Customer.delete_tax_id(cus_id, cus_obj['tax_ids']['data'][0]['id'])
        else:
            if form_data['abn']:
                stripe.Customer.create_tax_id(cus_id, type="au_abn", value=form_data['abn'])

        _ = stripe.Customer.modify(cus_id,
                                   name=form_data['name'],
                                   email=form_data['email'],
                                   address={'country': form_data['country'], 'state': form_data['state'],
                                            'postal_code': form_data['postal_code'], 'city': form_data['city'],
                                            'line1': form_data['line1'], 'line2': form_data['line2']})

        return json_success(json.dumps({'msg': 'Successfully changed billing detail!'}))

    @api
    @handle_api_exception
    @expose('/change_card_detail/<pm_id>/', methods=['POST'])
    def change_card_detail(self, pm_id):
        if self.update_ccard(pm_id, get_team_id()):
            return json_success(json.dumps({'msg': 'Credit card updated successful', 'pm_id': pm_id}))
        else:
            return json_error_response('Card update failed. Please try again later.')

    def update_ccard(self, pm_id, team_id):
        try:
            team = self.appbuilder.get_session.query(Team).filter_by(id=team_id).first()
            stripe.Customer.modify(team.stripe_user_id, source=pm_id)
            team.stripe_pm_id = pm_id
            self.appbuilder.get_session.commit()
            return True
        except Exception as e:
            logging.error(e)
            self.appbuilder.get_session.rollback()
            return False

    def update_plan(self, team_id, plan_stripe_id):
        try:
            '''Update payment methond ID, aka card id, if needed'''
            team = self.appbuilder.get_session.query(Team).filter_by(id=team_id).first()

            '''Update team subscription, and reduce used '''
            team_sub = self.appbuilder.sm.get_subscription(team_id=team.id)

            old_plan = self.appbuilder.get_session.query(Plan).filter_by(id=team_sub.plan).first()
            new_plan = self.appbuilder.get_session.query(Plan).filter_by(stripe_id=plan_stripe_id).first()

            current_subscription = stripe.Subscription.retrieve(team_sub.stripe_sub_id)
            # If upgrade plan, take effect immediately
            if new_plan.id > old_plan.id:
                logging.info(f'Upgrading team {team.team_name} from {old_plan.stripe_id} to {new_plan.stripe_id}')
                old_count = team_sub.remain_count

                # Disable free trial for future
                # team_sub.trial_used = True
                g.user.trial_used = True

                # Update the stripe subscription to new plan
                new_sub = stripe.Subscription.modify(current_subscription.stripe_id,
                                                     cancel_at_period_end=False,
                                                     trial_end='now',
                                                     items=[{
                                                         'id': current_subscription['items']['data'][0].id,
                                                         'plan': plan_stripe_id}])

                # If upgrading from paid plan to higher paid plan, cannot trigger payment succeeded event as it will be
                # on next billing cycle. Since the customer has successfully paid before, assume the card is still
                # valid, upgrade plan immediately
                if old_plan.id != 1:
                    logging.info('Customer paid before, upgrade immediately, prorate to next billing cycle')
                    team_sub.remain_count = old_count + new_plan.num_request - old_plan.num_request
                    team_sub.plan = new_plan.id

                    return_subscription_id = new_plan.stripe_id

                # Otherwise if upgrade from free to paid, then will trigger payment event, wait for event and let
                # webhook upgrade the plan
                else:
                    logging.info('Customer new to paid plan, will upgrade after payment succeeded')
                    # TODO: figure out better solution for updating from free to paid
                    return_subscription_id = new_plan.stripe_id

                # In case customer has downgrade before and want to upgrade again
                sub_list = stripe.Subscription.list(customer=team.stripe_user_id)
                if len(sub_list['data']) >= 2:
                    logging.info(f'Team {team.team_name} has downgraded before')
                    for sub in sub_list['data']:
                        if sub['id'] != current_subscription.stripe_id:
                            stripe.Subscription.delete(sub['id'])

                # log to mixpanel
                log_to_mp(g.user, team.team_name, 'upgrade plan', {
                    'old plan': old_plan.plan_name,
                    'new plan': new_plan.plan_name,
                })

                message = {
                    "first_name": g.user.first_name,
                    "plan_name": old_plan.plan_name,
                    "new_plan_name": new_plan.plan_name,
                    "num_request": old_count + new_plan.num_request - old_plan.num_request,
                    # "end_date": (date.today() + timedelta(30)).isoformat()
                    "end_date": str(datetime.fromtimestamp(new_sub['current_period_end']))
                }
                template_id = 'd-58fa993811e2490aac30a2acc047e08e'

            elif new_plan.id < old_plan.id:
                # get subscribe list for the team
                sub_list = stripe.Subscription.list(customer=team.stripe_user_id)
                # Set current subscribe to cancel at period end
                old_sub = stripe.Subscription.modify(current_subscription.stripe_id, cancel_at_period_end=True)
                # Record current period end and will be used as start for next plan
                period_end = old_sub['current_period_end']
                # Delete other plan if has more than one plan, which means downgraded before
                if len(sub_list['data']) >=2:
                    logging.info(f'Team {team.team_name} has downgraded before')
                    for sub in sub_list['data']:
                        if sub['id'] != current_subscription.stripe_id:
                            stripe.Subscription.delete(sub['id'])
                # Create new plan with trial end at beginning of next period
                new_sub = stripe.Subscription.create(customer=team.stripe_user_id, trial_end=period_end, items=[{
                    'plan': new_plan.stripe_id,
                    'quantity': '1',
                }])
                return_subscription_id = old_plan.stripe_id

                # log to mixpanel
                log_to_mp(g.user, team.team_name, 'downgrade plan', {
                    'old plan': old_plan.plan_name,
                    'new plan': new_plan.plan_name,
                })
                message = {
                    "first_name": g.user.first_name,
                    "plan_name": old_plan.plan_name,
                    "new_plan_name": new_plan.plan_name,
                }
                template_id = 'd-81ed56fd6c924e3b8337c3cce9fbd17b'

            else:
                return_subscription_id = None
            self.appbuilder.get_session.commit()

            _ = send_sendgrid_email(g.user, message, template_id)
            return True, return_subscription_id

        except Exception as e:
            self.appbuilder.get_session.rollback()
            logging.error(e)
            return False, None

    # #TODO for future, endpoint for on demmand payment
    # def on_demand_pay(self):
    #     pass

    @expose('/start_trial/', methods=['POST'])
    def start_trial(self):
        flag = False
        team = self.appbuilder.get_session.query(Team).filter_by(id=session['team_id']).first()
        for team_role in g.user.team_role:
            if team_role.team.id == team.id and team_role.role.name == 'team_owner':
                flag = True
                break

        if flag:
            try:
                # team = self.appbuilder.sm.find_team(user_id=g.user.id)
                team_sub = self.appbuilder.sm.get_subscription(team_id=team.id)
                if g.user.trial_used:
                    raise json_error_response('Already used trial.')
                stripe_sub = stripe.Subscription.retrieve(team_sub.stripe_sub_id)
                starter_plan = self.appbuilder.get_session.query(Plan).filter_by(id=2).first()

                utc_trial_end_ts = datetime.now().timestamp()
                subscription = stripe.Subscription.modify(stripe_sub.stripe_id,
                                                          trial_end=int(utc_trial_end_ts)+14*24*3600,
                                                          items=[{
                                                                'id': stripe_sub['items']['data'][0].id,
                                                                'plan': starter_plan.stripe_id,
                                                            }])
                g.user.trial_used = True
                team_sub.remain_count = starter_plan.num_request
                team_sub.plan = starter_plan.id
                team_sub.end_time = subscription['current_period_end']
                self.appbuilder.get_session.merge(g.user)
                self.appbuilder.get_session.commit()

                log_to_mp(g.user, team.team_name, 'start trial', {
                    'subscription id': team_sub.id,
                    'sub stripe id': team_sub.stripe_sub_id,
                    'trial end': team_sub.end_time,
                })

                template_id = 'd-db96cb2be4764a25bf8417f85c2045ba'

                send_sendgrid_email(g.user, {}, template_id)

                return json_success(json.dumps({
                    'msg': 'Start trial successfully! You have 14 days to use 7 advance searches.',
                    'remain_count': starter_plan.num_request,
                    'plan_id': 2,
                    'remain_days': 13,
                }))
            except ValueError as e:
                return json_error_response(e)
            except Exception as e:
                return json_error_response('Cannot start trial. Error: ' + str(e))
        else:
            return json_error_response('Cannot start trial for non-owner role.')

    def renew(self, event_object):
        paid_list = event_object['lines']['data']

        valid_item_index = 0
        # Check lines on the paid list
        if len(paid_list) > 1:
            logging.info('Contains more than one items in the invoice')
            # Find the paid plan with latest end time of subscription, use it to update database
            end_time = 0
            for i in range(0, paid_list):
                item = paid_list[i]
                logging.info(f'Customer {event_object["customer_name"]} Item {item["plan"]["nickname"]}')
                if item['amount'] >0 and item['period']['end'] > end_time:
                    end_time = item['period']['end']
                    valid_item_index = i

        try:
            stripe_plan = paid_list[valid_item_index]
            local_plan = self.appbuilder.get_session.query(Plan).filter_by(stripe_id=stripe_plan["plan"]['id']).first()

            # Fetch team_subscription by the subscription on invoice
            team_sub = self.appbuilder.sm.get_subscription(sub_id=stripe_plan['subscription'])

            # Set subscribed plan to the plan on the invoice, and reset remain count
            # This event should happen only when customer upgrade to paid from free for the first time and paid upfront,
            # or at the start of new billing cycle. So it is safe to reset.
            if team_sub is None:
                raise Exception('team subscription not found')
            team_sub.plan = local_plan.id
            team_sub.remain_count = local_plan.num_request
            team_sub.end_time = stripe_plan['period']['end']
            team = self.appbuilder.sm.find_team(team_id=team_sub.team)
            self.appbuilder.get_session.commit()

            log_to_mp(None, team.team_name, 'auto renew successful', {
                'plan': local_plan.plan_name,
            })

            # Mute renew for 0 peyment
            # TODO for customers with credits renewing plan is also 0
            if event_object['amount_paid'] > 0:
                user = self.appbuilder.sm.find_user(email=event_object["customer_email"])
                email_content = {
                    "first_name": user.first_name,
                    "plan_name": local_plan.plan_name,
                    "num_request": local_plan.num_request,
                    "end_date": (datetime.utcfromtimestamp(stripe_plan['period']['end']) + timedelta(hours=10)).date(
                    ).strftime('%d-%m-%Y')
                }
                template_id = 'd-884268c3f8cb4695ba1647c95a770aa1'

                send_sendgrid_email(user, email_content, template_id)

        except Exception as e:
            self.appbuilder.get_session.rollback()
            logging.warning(e)

    def revert_to_free(self, team):
        try:
            free_plan = self.appbuilder.get_session.query(Plan).filter_by(id=1).first()
            team_sub = self.appbuilder.sm.get_subscription(team_id=team.id)
            if team_sub is None:
                raise Exception('team subscription not found')
            logging.info('Downgrading stripe plan to free.')
            stripe_sub = stripe.Subscription.create(customer=team.stripe_user_id, items=[{
                'plan': free_plan.stripe_id,
                'quantity': '1',
            }])
            logging.info('Old subscription removed and free subscription created')
            logging.info(stripe_sub)
            team_sub.plan = free_plan.id
            team_sub.end_time = stripe_sub['current_period_end']
            team_sub.remain_count = 0
            team = self.appbuilder.sm.find_team(team_id=team_sub.team)
            log_to_mp(None, team.team_name, 'revert to free after 14 days', {})

            self.appbuilder.get_session.commit()
        except Exception as e:
            self.appbuilder.get_session.rollback()
            logging.warning(e)

    def payment_fail(self, event_object):
        try:
            logging.info(event_object)
            paid_list = event_object['lines']['data']
            stripe_plan = paid_list[0]
            # free_plan = self.appbuilder.get_session.query(Plan).filter_by(id=1).first()
            team_sub = self.appbuilder.get_session.query(TeamSubscription).filter_by(stripe_sub_id=stripe_plan['subscription']).first()

            team = self.appbuilder.sm.find_team(team_id=team_sub.team)
            log_to_mp(None, team.team_name, 'payment failed', {})

            # TODO send payment fail email
            template_id = 'd-fb23de7a3b914762be9011bd92a083cb'

            team_admin = self.appbuilder.sm.find_team_admin(team_id=team.id)

            send_sendgrid_email(team_admin, None, template_id)

        except Exception as e:
            logging.warning(e)

    def update_invoice_item_description(self, event_object):
        try:
            logging.info(event_object)
            team = self.appbuilder.get_session.query(Team).filter_by(stripe_user_id=event_object['customer']).first()
            plan_name = event_object['lines']['data'][0]['plan']['nickname']
            description = f'SolarBI {team.team_name} {plan_name}'
            logging.info(f'Monthly invoice description: {description}')
            _ = stripe.Invoice.modify(event_object['id'], statement_descriptor=description)
        except Exception as e:
            logging.warning(e)

    @api
    @expose('/webhook', methods=['POST'])
    def webhook(self):
        body = request.data
        try:
            event = stripe.Event.construct_from(
                json.loads(body), stripe.api_key
            )
        except ValueError as e:
            logging.warning(e)
            return Response(status=400)
        print(event.type)

        log = self.appbuilder.get_session.query(StripeEvent).filter_by(id=event['id']).first()
        if log is not None:
            logging.info('Duplicate event received: {}'.format(log.id))
        else:
            # need to log events by id
            log = StripeEvent()
            log.id = event.id
            log.Date = datetime.utcfromtimestamp(event['created'])
            log.Type = event.type
            log.Object = str(event['data']['object'])
            self.appbuilder.get_session.add(log)
            self.appbuilder.get_session.commit()
            if event.type == 'invoice.payment_succeeded':
                # print(event)
                self.renew(event['data']['object'])
            elif event.type == 'invoice.payment_failed':
                self.payment_fail(event['data']['object'])
            elif event.type == 'invoice.created':
                self.update_invoice_item_description(event['data']['object'])
        return Response(status=200)


appbuilder.add_view(
    SolarBIBillingView,
    'Billing',
    label=__('Billing'),
    icon='fa-save',
    category='Billing',
    category_label=__('Billing'),
    category_icon='fa-sun-o',
)


# class SolarBIDashboardView(ModelView):
#     route_base = '/solarbidashboard'
#     datamodel = SQLAInterface(models.SolarBISlice)
#     base_filters = [['viz_type', FilterEqual, 'solarBI'],
#                     ['team_id', FilterEqualFunction, get_team_id]]
#     # ['created_by', FilterEqualFunction, get_user]]
#     # base_permissions = ['can_list', 'can_show', 'can_add', 'can_delete', 'can_edit']
#
#     search_columns = (
#         'slice_name', 'description', 'owners',
#     )
#     list_columns = [
#         'slice_link', 'creator', 'modified', 'view_slice_name', 'view_slice_link',
#         'slice_query_id', 'slice_download_link', 'slice_id', 'changed_by_name'
#     ]
#     edit_columns = [
#         "slice_name",
#         "description",
#         "viz_type",
#         "owners",
#         "params",
#         "cache_timeout",
#     ]
#
#     order_columns = ['modified']
#
#     filters_not_for_admin = {}
#
#     list_template = 'solar/my_dashboard.html',
#     list_title = 'My Dashboard - SolarBI'
#     list_widget = SolarBIDashboardListWidget
#
#     @expose('/my-dashboard')
#     @has_access
#     def mydashboard(self):
#
#         for team_role in g.user.team_role:
#             role = team_role.role
#             if role.name == 'Admin':
#                 self.remove_filters_for_role(role.name)
#                 break
#             else:
#                 self.add_filters_for_role(role.name)
#         widgets = self._list()
#         return self.render_template(self.list_template,
#                                     title=self.list_title,
#                                     widgets=widgets)
#
#     def _get_list_widget(
#             self,
#             filters,
#             actions=None,
#             order_column="",
#             order_direction="",
#             page=None,
#             page_size=None,
#             widgets=None,
#             **args
#     ):
#         """ get joined base filter and current active filter for query """
#         # pylint: disable=unpacking-non-sequence
#         widgets = widgets or {}
#         actions = actions or self.actions
#         page_size = page_size or self.page_size
#         if not order_column and self.base_order:
#             order_column, order_direction = self.base_order
#         joined_filters = filters.get_joined_filters(self._base_filters)
#         count, lst = self.datamodel.query(
#             joined_filters,
#             order_column,
#             order_direction,
#             page=page,
#             page_size=page_size,
#         )
#         pks = self.datamodel.get_keys(lst)
#
#         # serialize composite pks
#         pks = [self._serialize_pk_if_composite(pk) for pk in pks]
#
#         all_object_keys = []
#         try:
#             all_object_keys = self.list_object_key('colin-query-test',
#                                                    'TID' + str(get_session_team(
#                                                        self.appbuilder.sm, g.user.id)[
#                                                                    0]) + '/')
#         except Exception:
#             pass
#
#         obj_keys = []
#         avail_object_keys = []
#         if all_object_keys:
#             avail_object_keys = [key for key in all_object_keys if key.endswith('.csv')]
#             obj_keys = [key.split('/')[2].replace('.csv', '') for key in
#                         avail_object_keys]
#
#         # Get current session team
#         session_team = get_session_team(self.appbuilder.sm, g.user.id)
#
#         # Get remaining advance requests in this billing period
#         subscription = self.appbuilder.sm.get_subscription(team_id=session_team[0])
#         remain_advanced_searches = subscription.remain_count
#         # Get the total number of advance requests in the history
#         value_generator = self.datamodel.get_values(lst, self.list_columns)
#         history_advance_count = len([item['slice_query_id'] for item in value_generator
#                                     if item['slice_query_id'] != 'None'])
#         # Get the number of team members
#         cur_team = self.appbuilder.sm.find_team(team_id=session_team[0])
#         awaiting_emails = self.appbuilder.sm.get_awaiting_emails(cur_team)
#         team_users = self.appbuilder.sm.get_team_members(cur_team.id)
#         team_users_count = len(cur_team.users)
#         # Get the number of new team members who joined in this week
#         new_team_users_count = self.appbuilder.sm.get_new_team_users_count(session_team[0])
#         # Get the current plan name
#         plan_name = self.appbuilder.get_session.query(Plan).filter_by(id=subscription.plan).first().plan_name
#
#         widgets["list"] = self.list_widget(
#             appbuilder=self.appbuilder,
#             session_team=session_team,
#             avail_object_keys=avail_object_keys,
#             obj_keys=obj_keys,
#             remain_advanced_searches=remain_advanced_searches,
#             history_advance_count=history_advance_count,
#             team_users_count=team_users_count,
#             new_team_users_count=new_team_users_count,
#             plan_name=plan_name,
#             format_datetime=format_datetime,
#             awaiting_emails=awaiting_emails,
#             team_users=team_users,
#             label_columns=self.label_columns,
#             include_columns=self.list_columns,
#             value_columns=itertools.islice(self.datamodel.get_values(lst, self.list_columns), 5),
#             order_columns=self.order_columns,
#             formatters_columns=self.formatters_columns,
#             page=page,
#             page_size=page_size,
#             count=count,
#             pks=pks,
#             actions=actions,
#             filters=filters,
#             modelview_name=self.__class__.__name__,
#         )
#         return widgets
#
#     def list_object_key(self, bucket, prefix):
#         AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
#         AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
#         session = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
#                                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
#         client = session.client('s3', region_name='ap-southeast-2')
#         key_list = []
#         response = client.list_objects_v2(
#             Bucket=bucket,
#             Prefix=prefix
#         )
#         contents = None
#         try:
#             contents = response['Contents']
#         except:
#             pass
#
#         is_truncated = response['IsTruncated']
#         for content in contents:
#             try:
#                 key_list.append(content['Key'])
#             except:
#                 pass
#
#         if is_truncated:
#             cont_token = response['NextContinuationToken']
#         while is_truncated:
#             response = client.list_objects_v2(
#                 Bucket=bucket,
#                 Prefix=prefix,
#                 ContinuationToken=cont_token
#             )
#             contents = response['Contents']
#             is_truncated = response['IsTruncated']
#             for content in contents:
#                 key_list.append(content['Key'])
#             if is_truncated:
#                 cont_token = response['NextContinuationToken']
#         return sorted(key_list)
#
#     def remove_filters_for_role(self, role_name):
#         if role_name == 'Admin':
#             self.remove_filter('created_by')
#
#     def add_filters_for_role(self, role_name):
#         if role_name != 'Admin':
#             self.add_filters('created_by')
#
#     def add_filters(self, filter_name):
#         for f in self.filters_not_for_admin:
#             if f.column_name == filter_name:
#                 self._base_filters.filters.append(f)
#                 self._base_filters.values.append(self.filters_not_for_admin[f])
#                 del self.filters_not_for_admin[f]
#                 break
#
#     def remove_filter(self, filter_name):
#         for f in self._base_filters.filters:
#             if f.column_name == filter_name:
#                 index_filter = self._base_filters.filters.index(f)
#                 value = self._base_filters.values[index_filter]
#                 self.filters_not_for_admin[f] = value
#                 self._base_filters.filters.remove(f)
#                 self._base_filters.values.remove(value)
#
#
# appbuilder.add_view(
#     SolarBIDashboardView,
#     'Dashboard',
#     label=__('Dashboard'),
#     icon='fa-save',
#     category='Dashboard',
#     category_label=__('Dashboard'),
#     category_icon='fa-sun-o',
# )


class SliceAsync(SliceModelView):  # noqa
    route_base = "/sliceasync"
    list_columns = [
        "id",
        "slice_link",
        "viz_type",
        "slice_name",
        "creator",
        "modified",
        "icons",
        "changed_on_humanized",
    ]
    label_columns = {"icons": " ", "slice_link": _("Chart")}


appbuilder.add_view_no_menu(SliceAsync)


class SliceAddView(SliceModelView):  # noqa
    route_base = "/sliceaddview"
    list_columns = [
        "id",
        "slice_name",
        "slice_url",
        "edit_url",
        "viz_type",
        "params",
        "description",
        "description_markeddown",
        "datasource_id",
        "datasource_type",
        "datasource_name_text",
        "datasource_link",
        "owners",
        "modified",
        "changed_on",
        "changed_on_humanized",
    ]


appbuilder.add_view_no_menu(SliceAddView)


class DashboardModelView(SupersetModelView, DeleteMixin):  # noqa
    route_base = "/dashboard"
    datamodel = SQLAInterface(models.Dashboard)

    list_title = _("Dashboards")
    show_title = _("Show Dashboard")
    add_title = _("Add Dashboard")
    edit_title = _("Edit Dashboard")

    list_columns = ["dashboard_link", "creator", "published", "modified"]
    order_columns = ["modified", "published"]
    edit_columns = [
        "dashboard_title",
        "slug",
        "owners",
        "position_json",
        "css",
        "json_metadata",
        "published",
    ]
    show_columns = edit_columns + ["table_names", "charts"]
    search_columns = ("dashboard_title", "slug", "owners", "published")
    add_columns = edit_columns
    base_order = ("changed_on", "desc")
    description_columns = {
        "position_json": _(
            "This json object describes the positioning of the widgets in "
            "the dashboard. It is dynamically generated when adjusting "
            "the widgets size and positions by using drag & drop in "
            "the dashboard view"
        ),
        "css": _(
            "The CSS for individual dashboards can be altered here, or "
            "in the dashboard view where changes are immediately "
            "visible"
        ),
        "slug": _("To get a readable URL for your dashboard"),
        "json_metadata": _(
            "This JSON object is generated dynamically when clicking "
            "the save or overwrite button in the dashboard view. It "
            "is exposed here for reference and for power users who may "
            "want to alter specific parameters."
        ),
        "owners": _("Owners is a list of users who can alter the dashboard."),
        "published": _(
            "Determines whether or not this dashboard is "
            "visible in the list of all dashboards"
        ),
    }
    base_filters = [["slice", DashboardFilter, lambda: []]]
    label_columns = {
        "dashboard_link": _("Dashboard"),
        "dashboard_title": _("Title"),
        "slug": _("Slug"),
        "charts": _("Charts"),
        "owners": _("Owners"),
        "creator": _("Creator"),
        "modified": _("Modified"),
        "position_json": _("Position JSON"),
        "css": _("CSS"),
        "json_metadata": _("JSON Metadata"),
        "table_names": _("Underlying Tables"),
    }

    def pre_add(self, obj):
        obj.slug = obj.slug or None
        if obj.slug:
            obj.slug = obj.slug.strip()
            obj.slug = obj.slug.replace(" ", "-")
            obj.slug = re.sub(r"[^\w\-]+", "", obj.slug)
        if g.user not in obj.owners:
            obj.owners.append(g.user)
        utils.validate_json(obj.json_metadata)
        utils.validate_json(obj.position_json)
        owners = [o for o in obj.owners]
        for slc in obj.slices:
            slc.owners = list(set(owners) | set(slc.owners))

    def pre_update(self, obj):
        check_ownership(obj)
        self.pre_add(obj)

    def pre_delete(self, obj):
        check_ownership(obj)

    @action("mulexport", __("Export"), __("Export dashboards?"), "fa-database")
    def mulexport(self, items):
        if not isinstance(items, list):
            items = [items]
        ids = "".join("&id={}".format(d.id) for d in items)
        return redirect("/dashboard/export_dashboards_form?{}".format(ids[1:]))

    @event_logger.log_this
    @has_access
    @expose("/export_dashboards_form")
    def download_dashboards(self):
        if request.args.get("action") == "go":
            ids = request.args.getlist("id")
            return Response(
                models.Dashboard.export_dashboards(ids),
                headers=generate_download_headers("json"),
                mimetype="application/text",
            )
        return self.render_template(
            "superset/export_dashboards.html", dashboards_url="/dashboard/list"
        )


appbuilder.add_view(
    DashboardModelView,
    "Dashboards",
    label=__("Dashboards"),
    icon="fa-dashboard",
    category="",
    category_icon="",
)


class DashboardModelViewAsync(DashboardModelView):  # noqa
    route_base = "/dashboardasync"
    list_columns = [
        "id",
        "dashboard_link",
        "creator",
        "modified",
        "dashboard_title",
        "changed_on",
        "url",
        "changed_by_name",
    ]
    label_columns = {
        "dashboard_link": _("Dashboard"),
        "dashboard_title": _("Title"),
        "creator": _("Creator"),
        "modified": _("Modified"),
    }


appbuilder.add_view_no_menu(DashboardModelViewAsync)


class DashboardAddView(DashboardModelView):  # noqa
    route_base = "/dashboardaddview"
    list_columns = [
        "id",
        "dashboard_link",
        "creator",
        "modified",
        "dashboard_title",
        "changed_on",
        "url",
        "changed_by_name",
    ]
    show_columns = list(set(DashboardModelView.edit_columns + list_columns))


appbuilder.add_view_no_menu(DashboardAddView)


@app.route("/health")
def health():
    return "OK"


@app.route("/healthcheck")
def healthcheck():
    return "OK"


@app.route("/ping")
def ping():
    return "OK"


class KV(BaseSupersetView):
    """Used for storing and retrieving key value pairs"""

    @event_logger.log_this
    @has_access_api
    @expose("/store/", methods=["POST"])
    def store(self):
        try:
            value = request.form.get("data")
            obj = models.KeyValue(value=value)
            db.session.add(obj)
            db.session.commit()
        except Exception as e:
            return json_error_response(e)
        return Response(json.dumps({"id": obj.id}), status=200)

    @event_logger.log_this
    @has_access_api
    @expose("/<key_id>/", methods=["GET"])
    def get_value(self, key_id):
        kv = None
        try:
            kv = db.session.query(models.KeyValue).filter_by(id=key_id).one()
        except Exception as e:
            return json_error_response(e)
        return Response(kv.value, status=200, content_type="text/plain")


appbuilder.add_view_no_menu(KV)


class R(BaseSupersetView):
    """used for short urls"""

    @event_logger.log_this
    @expose("/<url_id>")
    def index(self, url_id):
        url = db.session.query(models.Url).filter_by(id=url_id).first()
        if url and url.url:
            explore_url = "//superset/explore/?"
            if url.url.startswith(explore_url):
                explore_url += f"r={url_id}"
                return redirect(explore_url[1:])
            else:
                return redirect(url.url[1:])
        else:
            flash("URL to nowhere...", "danger")
            return redirect("/")

    @event_logger.log_this
    @has_access_api
    @expose("/shortner/", methods=["POST"])
    def shortner(self):
        url = request.form.get("data")
        obj = models.Url(url=url)
        db.session.add(obj)
        db.session.commit()
        return Response(
            "{scheme}://{request.headers[Host]}/r/{obj.id}".format(
                scheme=request.scheme, request=request, obj=obj
            ),
            mimetype="text/plain",
        )


appbuilder.add_view_no_menu(R)


class Superset(BaseSupersetView):
    """The base views for Superset!"""

    @has_access_api
    @expose("/datasources/")
    def datasources(self):
        datasources = ConnectorRegistry.get_all_datasources(db.session)
        datasources = [o.short_data for o in datasources if o.short_data.get("name")]
        datasources = sorted(datasources, key=lambda o: o["name"])
        return self.json_response(datasources)

    @has_access_api
    @expose("/override_role_permissions/", methods=["POST"])
    def override_role_permissions(self):
        """Updates the role with the give datasource permissions.

          Permissions not in the request will be revoked. This endpoint should
          be available to admins only. Expects JSON in the format:
           {
            'role_name': '{role_name}',
            'database': [{
                'datasource_type': '{table|druid}',
                'name': '{database_name}',
                'schema': [{
                    'name': '{schema_name}',
                    'datasources': ['{datasource name}, {datasource name}']
                }]
            }]
        }
        """
        data = request.get_json(force=True)
        role_name = data["role_name"]
        databases = data["database"]

        db_ds_names = set()
        for dbs in databases:
            for schema in dbs["schema"]:
                for ds_name in schema["datasources"]:
                    fullname = utils.get_datasource_full_name(
                        dbs["name"], ds_name, schema=schema["name"]
                    )
                    db_ds_names.add(fullname)

        existing_datasources = ConnectorRegistry.get_all_datasources(db.session)
        datasources = [d for d in existing_datasources if d.full_name in db_ds_names]
        role = security_manager.find_role(role_name)
        # remove all permissions
        role.permissions = []
        # grant permissions to the list of datasources
        granted_perms = []
        for datasource in datasources:
            view_menu_perm = security_manager.find_permission_view_menu(
                view_menu_name=datasource.perm, permission_name="datasource_access"
            )
            # prevent creating empty permissions
            if view_menu_perm and view_menu_perm.view_menu:
                role.permissions.append(view_menu_perm)
                granted_perms.append(view_menu_perm.view_menu.name)
        db.session.commit()
        return self.json_response(
            {"granted": granted_perms, "requested": list(db_ds_names)}, status=201
        )

    @event_logger.log_this
    @has_access
    @expose("/request_access/")
    def request_access(self):
        datasources = set()
        dashboard_id = request.args.get("dashboard_id")
        if dashboard_id:
            dash = (
                db.session.query(models.Dashboard).filter_by(id=int(dashboard_id)).one()
            )
            datasources |= dash.datasources
        datasource_id = request.args.get("datasource_id")
        datasource_type = request.args.get("datasource_type")
        if datasource_id:
            ds_class = ConnectorRegistry.sources.get(datasource_type)
            datasource = (
                db.session.query(ds_class).filter_by(id=int(datasource_id)).one()
            )
            datasources.add(datasource)

        has_access = all(
            (
                datasource and security_manager.datasource_access(datasource)
                for datasource in datasources
            )
        )
        if has_access:
            return redirect("/superset/dashboard/{}".format(dashboard_id))

        if request.args.get("action") == "go":
            for datasource in datasources:
                access_request = DAR(
                    datasource_id=datasource.id, datasource_type=datasource.type
                )
                db.session.add(access_request)
                db.session.commit()
            flash(__("Access was requested"), "info")
            return redirect("/")

        return self.render_template(
            "superset/request_access.html",
            datasources=datasources,
            datasource_names=", ".join([o.name for o in datasources]),
        )

    @event_logger.log_this
    @has_access
    @expose("/approve")
    def approve(self):
        def clean_fulfilled_requests(session):
            for r in session.query(DAR).all():
                datasource = ConnectorRegistry.get_datasource(
                    r.datasource_type, r.datasource_id, session)
                if not datasource or \
                   security_manager.datasource_access(datasource):

                    # datasource does not exist anymore
                    session.delete(r)
            session.commit()

        datasource_type = request.args.get('datasource_type')
        datasource_id = request.args.get('datasource_id')
        created_by_username = request.args.get('created_by')
        role_to_grant = request.args.get('role_to_grant')
        role_to_extend = request.args.get('role_to_extend')

        session = db.session
        datasource = ConnectorRegistry.get_datasource(
            datasource_type, datasource_id, session
        )

        if not datasource:
            flash(DATASOURCE_MISSING_ERR, "alert")
            return json_error_response(DATASOURCE_MISSING_ERR)

        requested_by = security_manager.find_user(username=created_by_username)
        if not requested_by:
            flash(USER_MISSING_ERR, "alert")
            return json_error_response(USER_MISSING_ERR)

        requests = (
            session.query(DAR).filter(
                DAR.datasource_id == datasource_id,
                DAR.datasource_type == datasource_type,
                DAR.created_by_fk == requested_by.id,
            ).all()
        )

        if not requests:
            flash(ACCESS_REQUEST_MISSING_ERR, "alert")
            return json_error_response(ACCESS_REQUEST_MISSING_ERR)

        # check if you can approve
        if security_manager.all_datasource_access() or check_ownership(
            datasource, raise_if_false=False
        ):
            # can by done by admin only
            if role_to_grant:
                role = security_manager.find_role(role_to_grant)
                requested_by.roles.append(role)
                msg = __(
                    "%(user)s was granted the role %(role)s that gives access "
                    "to the %(datasource)s",
                    user=requested_by.username,
                    role=role_to_grant,
                    datasource=datasource.full_name,
                )
                utils.notify_user_about_perm_udate(
                    g.user,
                    requested_by,
                    role,
                    datasource,
                    "email/role_granted.txt",
                    app.config,
                )
                flash(msg, "info")

            if role_to_extend:
                perm_view = security_manager.find_permission_view_menu(
                    "email/datasource_access", datasource.perm
                )
                role = security_manager.find_role(role_to_extend)
                security_manager.add_permission_role(role, perm_view)
                msg = __(
                    "Role %(r)s was extended to provide the access to "
                    "the datasource %(ds)s",
                    r=role_to_extend,
                    ds=datasource.full_name,
                )
                utils.notify_user_about_perm_udate(
                    g.user,
                    requested_by,
                    role,
                    datasource,
                    "email/role_extended.txt",
                    app.config,
                )
                flash(msg, "info")
            clean_fulfilled_requests(session)
        else:
            flash(__("You have no permission to approve this request"), "danger")
            return redirect("/accessrequestsmodelview/list/")
        for r in requests:
            session.delete(r)
        session.commit()
        return redirect("/accessrequestsmodelview/list/")

    def get_form_data(self, slice_id=None, use_slice_data=False):
        form_data = {}
        post_data = request.form.get("form_data")
        request_args_data = request.args.get("form_data")
        # Supporting POST
        if post_data:
            form_data.update(json.loads(post_data))
        # request params can overwrite post body
        if request_args_data:
            form_data.update(json.loads(request_args_data))

        url_id = request.args.get("r")
        if url_id:
            saved_url = db.session.query(models.Url).filter_by(id=url_id).first()
            if saved_url:
                url_str = parse.unquote_plus(
                    saved_url.url.split("?")[1][10:], encoding="utf-8", errors=None
                )
                url_form_data = json.loads(url_str)
                # allow form_date in request override saved url
                url_form_data.update(form_data)
                form_data = url_form_data

        form_data = {
            k: v for k, v in form_data.items() if k not in FORM_DATA_KEY_BLACKLIST
        }

        # When a slice_id is present, load from DB and override
        # the form_data from the DB with the other form_data provided
        slice_id = form_data.get("slice_id") or slice_id
        slc = None

        # Check if form data only contains slice_id
        contains_only_slc_id = not any(key != "slice_id" for key in form_data)

        # Include the slice_form_data if request from explore or slice calls
        # or if form_data only contains slice_id
        if slice_id and (use_slice_data or contains_only_slc_id):
            slc = db.session.query(models.Slice).filter_by(id=slice_id).one_or_none()
            if slc:
                slice_form_data = slc.form_data.copy()
                slice_form_data.update(form_data)
                form_data = slice_form_data

        update_time_range(form_data)

        return form_data, slc

    def get_viz(
        self,
        slice_id=None,
        form_data=None,
        datasource_type=None,
        datasource_id=None,
        force=False,
    ):
        if slice_id:
            slc = db.session.query(models.Slice).filter_by(id=slice_id).one()
            return slc.get_viz()
        else:
            viz_type = form_data.get("viz_type", "table")
            datasource = ConnectorRegistry.get_datasource(
                datasource_type, datasource_id, db.session
            )
            viz_obj = viz.viz_types[viz_type](
                datasource, form_data=form_data, force=force
            )
            return viz_obj

    @has_access
    @expose("/slice/<slice_id>/")
    def slice(self, slice_id):
        form_data, slc = get_form_data(slice_id, use_slice_data=True)
        if not slc:
            abort(404)
        endpoint = "/superset/explore/?form_data={}".format(
            parse.quote(json.dumps({"slice_id": slice_id}))
        )
        if request.args.get("standalone") == "true":
            endpoint += "&standalone=true"
        return redirect(endpoint)

    def get_query_string_response(self, viz_obj):
        query = None
        try:
            query_obj = viz_obj.query_obj()
            if query_obj:
                query = viz_obj.datasource.get_query_str(query_obj)
        except Exception as e:
            logging.exception(e)
            return json_error_response(e)

        if not query:
            query = "No query."

        return self.json_response(
            {"query": query, "language": viz_obj.datasource.query_language}
        )

    def get_raw_results(self, viz_obj):
        return self.json_response(
            {"data": viz_obj.get_df_payload()["df"].to_dict("records")}
        )

    def get_samples(self, viz_obj):
        return self.json_response({"data": viz_obj.get_samples()})

    def generate_json(
        self, viz_obj, csv=False, query=False, results=False, samples=False
    ):
        if csv:
            return CsvResponse(
                viz_obj.get_csv(),
                status=200,
                headers=generate_download_headers("csv"),
                mimetype="application/csv",
            )

        if query:
            return self.get_query_string_response(viz_obj)

        if results:
            return self.get_raw_results(viz_obj)

        if samples:
            return self.get_samples(viz_obj)

        payload = viz_obj.get_payload()
        return data_payload_response(*viz_obj.payload_json_and_has_error(payload))

    @event_logger.log_this
    @api
    @has_access_api
    @expose("/slice_json/<slice_id>")
    @etag_cache(CACHE_DEFAULT_TIMEOUT, check_perms=check_slice_perms)
    def slice_json(self, slice_id):
        form_data, slc = get_form_data(slice_id, use_slice_data=True)
        datasource_type = slc.datasource.type
        datasource_id = slc.datasource.id
        viz_obj = get_viz(
            datasource_type=datasource_type,
            datasource_id=datasource_id,
            form_data=form_data,
            force=False,
        )
        return self.generate_json(viz_obj)

    @event_logger.log_this
    @api
    @has_access_api
    @expose("/annotation_json/<layer_id>")
    def annotation_json(self, layer_id):
        form_data = get_form_data()[0]
        form_data["layer_id"] = layer_id
        form_data["filters"] = [{"col": "layer_id", "op": "==", "val": layer_id}]
        datasource = AnnotationDatasource()
        viz_obj = viz.viz_types["table"](datasource, form_data=form_data, force=False)
        payload = viz_obj.get_payload()
        return data_payload_response(*viz_obj.payload_json_and_has_error(payload))

    EXPLORE_JSON_METHODS = ["POST"]
    if not is_feature_enabled("ENABLE_EXPLORE_JSON_CSRF_PROTECTION"):
        EXPLORE_JSON_METHODS.append("GET")

    @event_logger.log_this
    @api
    @has_access_api
    @handle_api_exception
    @expose(
        "/explore_json/<datasource_type>/<datasource_id>/", methods=EXPLORE_JSON_METHODS
    )
    @expose("/explore_json/", methods=EXPLORE_JSON_METHODS)
    @etag_cache(CACHE_DEFAULT_TIMEOUT, check_perms=check_datasource_perms)
    def explore_json(self, datasource_type=None, datasource_id=None):
        """Serves all request that GET or POST form_data

        This endpoint evolved to be the entry point of many different
        requests that GETs or POSTs a form_data.

        `self.generate_json` receives this input and returns different
        payloads based on the request args in the first block

        TODO: break into one endpoint for each return shape"""
        csv = request.args.get("csv") == "true"
        query = request.args.get("query") == "true"
        results = request.args.get("results") == "true"
        samples = request.args.get("samples") == "true"
        force = request.args.get("force") == "true"

        form_data = get_form_data()[0]


        try:
            datasource_id, datasource_type = get_datasource_info(
                datasource_id, datasource_type, form_data
            )
        except SupersetException as e:
            return json_error_response(utils.error_msg_from_exception(e))

        viz_obj = get_viz(
            datasource_type=datasource_type,
            datasource_id=datasource_id,
            form_data=form_data,
            force=force,
        )

        log_to_mp(g.user, session['team_name'], 'explore json', {})

        return self.generate_json(
            viz_obj, csv=csv, query=query, results=results, samples=samples
        )

    def send_email(self, user, address_name):
        """
            Method for sending the Email to the user
        """
        log = logging.getLogger(__name__)
        dynamic_template_data = {
            'first_name': user.first_name,
            'address_name': address_name,
        }
        template_id = 'd-d9166982344e4054a583d9b7b6ccec56'

        return send_sendgrid_email(user, dynamic_template_data, template_id)

    @event_logger.log_this
    @api
    @handle_api_exception
    @expose('/request_data/<lat>/<lng>/<start_date>/<end_date>/<resolution>/<address_name>/<generation>/<unit>/'
            '<cap1>/<cap2>/<cap3>/', methods=['GET', 'POST'])
    def request_data(self, lat=None, lng=None, start_date=None, end_date=None, resolution=None, address_name=None,
                     generation=None, unit=None, cap1=None, cap2=None, cap3=None):
        """Serves all request that GET or POST form_data

        This endpoint evolved to be the entry point of many different
        requests that GETs or POSTs a form_data."""
        try:
            # Check whether the team has available requests. If there is no remaining request, then return an
            # error json message, otherwise subtract the remaining requests by 1
            team = self.appbuilder.sm.find_team(team_id=get_session_team(self.appbuilder.sm, g.user.id)[0])
            subscription = self.appbuilder.sm.get_subscription(team_id=team.id)
            if subscription.remain_count <= 0:
                return json_error_response("You cannot request any more data.")
            else:
                subscription.remain_count = subscription.remain_count - 1
                self.appbuilder.get_session.commit()

            # Start call the api to request solar radiation data and compute the generation
            url = os.environ["GENERATION_API"]
            if cap2 == '0':
                capacity_list = ", 'capacity': [" + cap1
            elif cap3 == '0':
                capacity_list = ", 'capacity': [" + cap1 + ", " + cap2
            else:
                capacity_list = ", 'capacity': [" + cap1 + ", " + cap2 + ", " + cap3
            payload = "{'start_date': '" + start_date + "', 'end_date': '" + end_date + "', 'lat': " + lat + \
                      ", 'lng': " + lng + ", 'bucket': 'colin-query-test', " \
                      "'team_id': '" + str(get_session_team(self.appbuilder.sm, g.user.id)[0]) + \
                      "', 'email': '" + g.user.email + "', 'resolution': '" + resolution + \
                      "', 'generation': " + generation + capacity_list + \
                      "], 'capacity_unit': '" + unit + "'}"
            response = requests.request("POST", url, data=payload)
            response = json.loads(response.text)

            # athena_query = get_athena_query(lat, lng, start_date, end_date, type, resolution)
            # AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
            # AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
            # session = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
            #                                 aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
            # client = session.client('athena', region_name='ap-southeast-2')
            # response = client.start_query_execution(
            #     QueryString=athena_query,
            #     QueryExecutionContext={
            #         'Database': 'solar_radiation_hill'
            #     },
            #     ResultConfiguration={
            #         'OutputLocation': 's3://colin-query-test/TID' +
            #                           str(get_session_team(self.appbuilder.sm, g.user.id)[0]) +
            #                           '/'test + g.user.email,
            #         # 'EncryptionConfiguration': {
            #         #     'EncryptionOption': 'SSE_S3',
            #         #     'KmsKey': 'string'
            #         # }
            #     },
            # )

            # Save the query details in the database
            form_data = get_form_data()[0]
            args = {'action': 'saveas',
                    'slice_name': address_name + '_' + form_data['startDate'] + '_' +
                                  form_data['endDate'] + '_both_' + resolution}
            datasource = ConnectorRegistry.get_datasource(
                form_data['datasource_type'], form_data['datasource_id'], db.session)
            self.save_or_overwrite_solarbislice(args, None, True, None, False, form_data['datasource_id'],
                                                form_data['datasource_type'], datasource.name,
                                                # query_id=response['QueryExecutionId'],
                                                query_id=response['query_id'],
                                                start_date=form_data['startDate'],
                                                end_date=form_data['endDate'], data_type='both', resolution=resolution)

            # After data request success and save db success, send user a job received email
            self.send_email(g.user, address_name)
            # Then log this event into Mixpanel
            log_to_mp(g.user, team.team_name, 'request data', {
                'lat': lat,
                'lng': lng,
                'start date': start_date,
                'end date': end_date,
                'resulution': resolution,
                'type': 'both',
                'address': address_name,
            })
            # return json_success(json.dumps({'query_id': response['QueryExecutionId']}))
            return json_success(json.dumps({'query_id': response['query_id']}))
        except Exception:
            return json_error_response("Request failed.")

    @event_logger.log_this
    @has_access
    @expose("/import_dashboards", methods=["GET", "POST"])
    def import_dashboards(self):
        """Overrides the dashboards using json instances from the file."""
        f = request.files.get("file")
        if request.method == "POST" and f:
            try:
                dashboard_import_export.import_dashboards(db.session, f.stream)
            except DatabaseNotFound as e:
                flash(
                    _(
                        "Cannot import dashboard: %(db_error)s.\n"
                        "Make sure to create the database before "
                        "importing the dashboard.",
                        db_error=e,
                    ),
                    "danger",
                )
            except Exception:
                flash(
                    _(
                        "An unknown error occurred. "
                        "Please contact your Superset administrator"
                    ),
                    "danger",
                )
            return redirect("/dashboard/list/")
        return self.render_template("superset/import_dashboards.html")

    @event_logger.log_this
    @has_access
    @expose("/explorev2/<datasource_type>/<datasource_id>/")
    def explorev2(self, datasource_type, datasource_id):
        """Deprecated endpoint, here for backward compatibility of urls"""
        return redirect(
            url_for(
                "Superset.explore",
                datasource_type=datasource_type,
                datasource_id=datasource_id,
                **request.args,
            )
        )

    @event_logger.log_this
    @has_access
    @expose("/explore/<datasource_type>/<datasource_id>/", methods=["GET", "POST"])
    @expose("/explore/", methods=["GET", "POST"])
    def explore(self, datasource_type=None, datasource_id=None):
        user_id = g.user.get_id() if g.user else None
        form_data, slc = get_form_data(use_slice_data=True)
        error_redirect = "/chart/list/"

        try:
            datasource_id, datasource_type = get_datasource_info(
                datasource_id, datasource_type, form_data
            )
        except SupersetException:
            return redirect(error_redirect)

        datasource = ConnectorRegistry.get_datasource(
            datasource_type, datasource_id, db.session
        )
        if not datasource:
            flash(DATASOURCE_MISSING_ERR, "danger")
            return redirect(error_redirect)

        if config.get("ENABLE_ACCESS_REQUEST") and (
            not security_manager.datasource_access(datasource)
        ):
            flash(
                __(security_manager.get_datasource_access_error_msg(datasource)),
                "danger",
            )
            return redirect(
                "superset/request_access/?"
                f"datasource_type={datasource_type}&"
                f"datasource_id={datasource_id}&"
            )

        viz_type = form_data.get("viz_type")
        if not viz_type and datasource.default_endpoint:
            return redirect(datasource.default_endpoint)

        # slc perms
        slice_add_perm = security_manager.can_access("can_add", "SliceModelView")
        slice_overwrite_perm = is_owner(slc, g.user)
        slice_download_perm = security_manager.can_access(
            "can_download", "SliceModelView"
        )

        form_data["datasource"] = str(datasource_id) + "__" + datasource_type

        # On explore, merge legacy and extra filters into the form data
        utils.convert_legacy_filters_into_adhoc(form_data)
        utils.merge_extra_filters(form_data)

        # merge request url params
        if request.method == "GET":
            utils.merge_request_params(form_data, request.args)

        # handle save or overwrite
        action = request.args.get("action")

        if action == "overwrite" and not slice_overwrite_perm:
            return json_error_response(
                _("You don't have the rights to ") + _("alter this ") + _("chart"),
                status=400,
            )

        if action == "saveas" and not slice_add_perm:
            return json_error_response(
                _("You don't have the rights to ") + _("create a ") + _("chart"),
                status=400,
            )

        if action in ("saveas", "overwrite"):
            return self.save_or_overwrite_slice(
                request.args,
                slc,
                slice_add_perm,
                slice_overwrite_perm,
                slice_download_perm,
                datasource_id,
                datasource_type,
                datasource.name,
            )

        standalone = request.args.get("standalone") == "true"
        bootstrap_data = {
            "can_add": slice_add_perm,
            "can_download": slice_download_perm,
            "can_overwrite": slice_overwrite_perm,
            "datasource": datasource.data,
            "form_data": form_data,
            "datasource_id": datasource_id,
            "datasource_type": datasource_type,
            "slice": slc.data if slc else None,
            "standalone": standalone,
            "user_id": user_id,
            "forced_height": request.args.get("height"),
            "common": self.common_bootstrap_payload(),
        }
        table_name = (
            datasource.table_name
            if datasource_type == "table"
            else datasource.datasource_name
        )
        if slc:
            title = slc.slice_name
        else:
            title = _("Explore - %(table)s", table=table_name)
        return self.render_template(
            "superset/basic.html",
            bootstrap_data=json.dumps(bootstrap_data),
            entry="explore",
            title=title,
            standalone_mode=standalone,
        )

    @api
    @handle_api_exception
    @has_access_api
    @expose("/filter/<datasource_type>/<datasource_id>/<column>/")
    def filter(self, datasource_type, datasource_id, column):
        """
        Endpoint to retrieve values for specified column.

        :param datasource_type: Type of datasource e.g. table
        :param datasource_id: Datasource id
        :param column: Column name to retrieve values for
        :return:
        """
        # TODO: Cache endpoint by user, datasource and column
        datasource = ConnectorRegistry.get_datasource(
            datasource_type, datasource_id, db.session
        )
        if not datasource:
            return json_error_response(DATASOURCE_MISSING_ERR)
        security_manager.assert_datasource_permission(datasource)
        payload = json.dumps(
            datasource.values_for_column(
                column, config.get("FILTER_SELECT_ROW_LIMIT", 10000)
            ),
            default=utils.json_int_dttm_ser,
        )
        return json_success(payload)

    def save_or_overwrite_slice(
        self,
        args,
        slc,
        slice_add_perm,
        slice_overwrite_perm,
        slice_download_perm,
        datasource_id,
        datasource_type,
        datasource_name,
    ):
        """Save or overwrite a slice"""
        slice_name = args.get("slice_name")
        action = args.get("action")
        form_data = get_form_data()[0]

        if action in ("saveas"):
            if "slice_id" in form_data:
                form_data.pop("slice_id")  # don't save old slice_id
            slc = models.Slice(owners=[g.user] if g.user else [])

        slc.params = json.dumps(form_data, indent=2, sort_keys=True)
        slc.datasource_name = datasource_name
        slc.viz_type = form_data["viz_type"]
        slc.datasource_type = datasource_type
        slc.datasource_id = datasource_id
        slc.slice_name = slice_name

        if action in ("saveas") and slice_add_perm:
            self.save_slice(slc)
        elif action == "overwrite" and slice_overwrite_perm:
            self.overwrite_slice(slc)

        # Adding slice to a dashboard if requested
        dash = None
        if request.args.get("add_to_dash") == "existing":
            dash = (
                db.session.query(models.Dashboard)
                .filter_by(id=int(request.args.get("save_to_dashboard_id")))
                .one()
            )

            # check edit dashboard permissions
            dash_overwrite_perm = check_ownership(dash, raise_if_false=False)
            if not dash_overwrite_perm:
                return json_error_response(
                    _("You don't have the rights to ")
                    + _("alter this ")
                    + _("dashboard"),
                    status=400,
                )

            flash(
                _("Chart [{}] was added to dashboard [{}]").format(
                    slc.slice_name, dash.dashboard_title
                ),
                "info",
            )
        elif request.args.get("add_to_dash") == "new":
            # check create dashboard permissions
            dash_add_perm = security_manager.can_access("can_add", "DashboardModelView")
            if not dash_add_perm:
                return json_error_response(
                    _("You don't have the rights to ")
                    + _("create a ")
                    + _("dashboard"),
                    status=400,
                )

            dash = models.Dashboard(
                dashboard_title=request.args.get("new_dashboard_name"),
                owners=[g.user] if g.user else [],
            )
            flash(
                _(
                    "Dashboard [{}] just got created and chart [{}] was added " "to it"
                ).format(dash.dashboard_title, slc.slice_name),
                "info",
            )

        if dash and slc not in dash.slices:
            dash.slices.append(slc)
            db.session.commit()

        response = {
            "can_add": slice_add_perm,
            "can_download": slice_download_perm,
            "can_overwrite": is_owner(slc, g.user),
            "form_data": slc.form_data,
            "slice": slc.data,
            "dashboard_id": dash.id if dash else None,
        }

        if request.args.get("goto_dash") == "true":
            response.update({"dashboard": dash.url})

        return json_success(json.dumps(response))

    def save_slice(self, slc, paid=False):
        session = db.session()
        # if not paid:
        #     msg = _("Your quick result record for [{}] has been saved.").format(slc.slice_name)
        if paid:
            msg = _("Success! A confirmation email has been sent to you. This record is also saved below.").format(slc.slice_name)
        session.add(slc)
        session.commit()
        if paid:
            flash(msg, "info")

    def overwrite_slice(self, slc):
        session = db.session()
        session.merge(slc)
        session.commit()
        msg = _("Chart [{}] has been overwritten").format(slc.slice_name)
        flash(msg, "info")

    @api
    @has_access_api
    @expose("/checkbox/<model_view>/<id_>/<attr>/<value>", methods=["GET"])
    def checkbox(self, model_view, id_, attr, value):
        """endpoint for checking/unchecking any boolean in a sqla model"""
        modelview_to_model = {
            "{}ColumnInlineView".format(name.capitalize()): source.column_class
            for name, source in ConnectorRegistry.sources.items()
        }
        model = modelview_to_model[model_view]
        col = db.session.query(model).filter_by(id=id_).first()
        checked = value == "true"
        if col:
            setattr(col, attr, checked)
            if checked:
                metrics = col.get_metrics().values()
                col.datasource.add_missing_metrics(metrics)
            db.session.commit()
        return json_success('"OK"')

    @api
    @has_access_api
    @expose("/schemas/<db_id>/")
    @expose("/schemas/<db_id>/<force_refresh>/")
    def schemas(self, db_id, force_refresh="false"):
        db_id = int(db_id)
        force_refresh = force_refresh.lower() == "true"
        database = db.session.query(models.Database).filter_by(id=db_id).first()
        if database:
            schemas = database.get_all_schema_names(
                cache=database.schema_cache_enabled,
                cache_timeout=database.schema_cache_timeout,
                force=force_refresh,
            )
            schemas = security_manager.schemas_accessible_by_user(database, schemas)
        else:
            schemas = []

        return Response(json.dumps({"schemas": schemas}), mimetype="application/json")

    @api
    @has_access_api
    @expose("/tables/<db_id>/<schema>/<substr>/")
    @expose("/tables/<db_id>/<schema>/<substr>/<force_refresh>/")
    def tables(self, db_id, schema, substr, force_refresh="false"):
        """Endpoint to fetch the list of tables for given database"""
        db_id = int(db_id)
        force_refresh = force_refresh.lower() == "true"
        schema = utils.parse_js_uri_path_item(schema, eval_undefined=True)
        substr = utils.parse_js_uri_path_item(substr, eval_undefined=True)
        database = db.session.query(models.Database).filter_by(id=db_id).one()

        if schema:
            tables = (
                database.get_all_table_names_in_schema(
                    schema=schema,
                    force=force_refresh,
                    cache=database.table_cache_enabled,
                    cache_timeout=database.table_cache_timeout,
                )
                or []
            )
            views = (
                database.get_all_view_names_in_schema(
                    schema=schema,
                    force=force_refresh,
                    cache=database.table_cache_enabled,
                    cache_timeout=database.table_cache_timeout,
                )
                or []
            )
        else:
            tables = database.get_all_table_names_in_database(
                cache=True, force=False, cache_timeout=24 * 60 * 60
            )
            views = database.get_all_view_names_in_database(
                cache=True, force=False, cache_timeout=24 * 60 * 60
            )
        tables = security_manager.get_datasources_accessible_by_user(
            database, tables, schema
        )
        views = security_manager.get_datasources_accessible_by_user(
            database, views, schema
        )

        def get_datasource_label(ds_name: utils.DatasourceName) -> str:
            return ds_name.table if schema else f"{ds_name.schema}.{ds_name.table}"

        if substr:
            tables = [tn for tn in tables if substr in get_datasource_label(tn)]
            views = [vn for vn in views if substr in get_datasource_label(vn)]

        if not schema and database.default_schemas:
            user_schema = g.user.email.split("@")[0]
            valid_schemas = set(database.default_schemas + [user_schema])

            tables = [tn for tn in tables if tn.schema in valid_schemas]
            views = [vn for vn in views if vn.schema in valid_schemas]

        max_items = config.get("MAX_TABLE_NAMES") or len(tables)
        total_items = len(tables) + len(views)
        max_tables = len(tables)
        max_views = len(views)
        if total_items and substr:
            max_tables = max_items * len(tables) // total_items
            max_views = max_items * len(views) // total_items

        table_options = [
            {
                "value": tn.table,
                "schema": tn.schema,
                "label": get_datasource_label(tn),
                "title": get_datasource_label(tn),
            }
            for tn in tables[:max_tables]
        ]
        table_options.extend(
            [
                {
                    "value": vn.table,
                    "schema": vn.schema,
                    "label": f"[view] {get_datasource_label(vn)}",
                    "title": f"[view] {get_datasource_label(vn)}",
                }
                for vn in views[:max_views]
            ]
        )
        payload = {"tableLength": len(tables) + len(views), "options": table_options}
        return json_success(json.dumps(payload))

    @api
    @has_access_api
    @expose("/copy_dash/<dashboard_id>/", methods=["GET", "POST"])
    def copy_dash(self, dashboard_id):
        """Copy dashboard"""
        session = db.session()
        data = json.loads(request.form.get("data"))
        dash = models.Dashboard()
        original_dash = (
            session.query(models.Dashboard).filter_by(id=dashboard_id).first()
        )

        dash.owners = [g.user] if g.user else []
        dash.dashboard_title = data["dashboard_title"]

        if data["duplicate_slices"]:
            # Duplicating slices as well, mapping old ids to new ones
            old_to_new_sliceids = {}
            for slc in original_dash.slices:
                new_slice = slc.clone()
                new_slice.owners = [g.user] if g.user else []
                session.add(new_slice)
                session.flush()
                new_slice.dashboards.append(dash)
                old_to_new_sliceids["{}".format(slc.id)] = "{}".format(new_slice.id)

            # update chartId of layout entities
            # in v2_dash positions json data, chartId should be integer,
            # while in older version slice_id is string type
            for value in data["positions"].values():
                if (
                    isinstance(value, dict)
                    and value.get("meta")
                    and value.get("meta").get("chartId")
                ):
                    old_id = "{}".format(value.get("meta").get("chartId"))
                    new_id = int(old_to_new_sliceids[old_id])
                    value["meta"]["chartId"] = new_id
        else:
            dash.slices = original_dash.slices
        dash.params = original_dash.params

        self._set_dash_metadata(dash, data)
        session.add(dash)
        session.commit()
        dash_json = json.dumps(dash.data)
        session.close()
        return json_success(dash_json)

    @api
    @has_access_api
    @expose("/save_dash/<dashboard_id>/", methods=["GET", "POST"])
    def save_dash(self, dashboard_id):
        """Save a dashboard's metadata"""
        session = db.session()
        dash = session.query(models.Dashboard).filter_by(id=dashboard_id).first()
        check_ownership(dash, raise_if_false=True)
        data = json.loads(request.form.get("data"))
        self._set_dash_metadata(dash, data)
        session.merge(dash)
        session.commit()
        session.close()
        return json_success(json.dumps({"status": "SUCCESS"}))

    @staticmethod
    def _set_dash_metadata(dashboard, data):
        positions = data["positions"]
        # find slices in the position data
        slice_ids = []
        slice_id_to_name = {}
        for value in positions.values():
            if isinstance(value, dict):
                try:
                    slice_id = value["meta"]["chartId"]
                    slice_ids.append(slice_id)
                    slice_id_to_name[slice_id] = value["meta"]["sliceName"]
                except KeyError:
                    pass

        session = db.session()
        Slice = models.Slice  # noqa
        current_slices = session.query(Slice).filter(Slice.id.in_(slice_ids)).all()

        dashboard.slices = current_slices

        # update slice names. this assumes user has permissions to update the slice
        # we allow user set slice name be empty string
        for slc in dashboard.slices:
            try:
                new_name = slice_id_to_name[slc.id]
                if slc.slice_name != new_name:
                    slc.slice_name = new_name
                    session.merge(slc)
                    session.flush()
            except KeyError:
                pass

        # remove leading and trailing white spaces in the dumped json
        dashboard.position_json = json.dumps(
            positions, indent=None, separators=(",", ":"), sort_keys=True
        )
        md = dashboard.params_dict
        dashboard.css = data.get("css")
        dashboard.dashboard_title = data["dashboard_title"]

        if "filter_immune_slices" not in md:
            md["filter_immune_slices"] = []
        if "timed_refresh_immune_slices" not in md:
            md["timed_refresh_immune_slices"] = []
        if "filter_immune_slice_fields" not in md:
            md["filter_immune_slice_fields"] = {}
        md["expanded_slices"] = data["expanded_slices"]
        md["refresh_frequency"] = data.get("refresh_frequency", 0)
        default_filters_data = json.loads(data.get("default_filters", "{}"))
        applicable_filters = {
            key: v for key, v in default_filters_data.items() if int(key) in slice_ids
        }
        md["default_filters"] = json.dumps(applicable_filters)
        if data.get("color_namespace"):
            md["color_namespace"] = data.get("color_namespace")
        if data.get("color_scheme"):
            md["color_scheme"] = data.get("color_scheme")
        if data.get("label_colors"):
            md["label_colors"] = data.get("label_colors")
        dashboard.json_metadata = json.dumps(md)

    @api
    @has_access_api
    @expose("/add_slices/<dashboard_id>/", methods=["POST"])
    def add_slices(self, dashboard_id):
        """Add and save slices to a dashboard"""
        data = json.loads(request.form.get("data"))
        session = db.session()
        Slice = models.Slice  # noqa
        dash = session.query(models.Dashboard).filter_by(id=dashboard_id).first()
        check_ownership(dash, raise_if_false=True)
        new_slices = session.query(Slice).filter(Slice.id.in_(data["slice_ids"]))
        dash.slices += new_slices
        session.merge(dash)
        session.commit()
        session.close()
        return "SLICES ADDED"

    @api
    @has_access_api
    @expose("/testconn", methods=["POST", "GET"])
    def testconn(self):
        """Tests a sqla connection"""
        try:
            db_name = request.json.get("name")
            uri = request.json.get("uri")

            # if the database already exists in the database, only its safe (password-masked) URI
            # would be shown in the UI and would be passed in the form data.
            # so if the database already exists and the form was submitted with the safe URI,
            # we assume we should retrieve the decrypted URI to test the connection.
            if db_name:
                existing_database = (
                    db.session.query(models.Database)
                    .filter_by(database_name=db_name)
                    .first()
                )
                if existing_database and uri == existing_database.safe_sqlalchemy_uri():
                    uri = existing_database.sqlalchemy_uri_decrypted

            # this is the database instance that will be tested
            database = models.Database(
                # extras is sent as json, but required to be a string in the Database model
                extra=json.dumps(request.json.get("extras", {})),
                impersonate_user=request.json.get("impersonate_user"),
            )
            database.set_sqlalchemy_uri(uri)

            username = g.user.username if g.user is not None else None
            engine = database.get_sqla_engine(user_name=username)

            with closing(engine.connect()) as conn:
                conn.scalar(select([1]))
                return json_success('"OK"')
        except Exception as e:
            logging.exception(e)
            return json_error_response(
                "Connection failed!\n\n" "The error message returned was:\n{}".format(e)
            )

    @api
    @has_access_api
    @expose("/recent_activity/<user_id>/", methods=["GET"])
    def recent_activity(self, user_id):
        """Recent activity (actions) for a given user"""
        M = models  # noqa

        if request.args.get("limit"):
            limit = int(request.args.get("limit"))
        else:
            limit = 1000

        qry = (
            db.session.query(M.Log, M.Dashboard, M.Slice)
            .outerjoin(M.Dashboard, M.Dashboard.id == M.Log.dashboard_id)
            .outerjoin(M.Slice, M.Slice.id == M.Log.slice_id)
            .filter(
                and_(
                    ~M.Log.action.in_(("queries", "shortner", "sql_json")),
                    M.Log.user_id == user_id,
                )
            )
            .order_by(M.Log.dttm.desc())
            .limit(limit)
        )
        payload = []
        for log in qry.all():
            item_url = None
            item_title = None
            if log.Dashboard:
                item_url = log.Dashboard.url
                item_title = log.Dashboard.dashboard_title
            elif log.Slice:
                item_url = log.Slice.slice_url
                item_title = log.Slice.slice_name

            payload.append(
                {
                    "action": log.Log.action,
                    "item_url": item_url,
                    "item_title": item_title,
                    "time": log.Log.dttm,
                }
            )
        return json_success(json.dumps(payload, default=utils.json_int_dttm_ser))

    @api
    @has_access_api
    @expose("/csrf_token/", methods=["GET"])
    def csrf_token(self):
        return Response(
            self.render_template("superset/csrf_token.json"), mimetype="text/json"
        )

    @api
    @has_access_api
    @expose("/available_domains/", methods=["GET"])
    def available_domains(self):
        """
        Returns the list of available Superset Webserver domains (if any)
        defined in config. This enables charts embedded in other apps to
        leverage domain sharding if appropriately configured.
        """
        return Response(
            json.dumps(conf.get("SUPERSET_WEBSERVER_DOMAINS")), mimetype="text/json"
        )

    @api
    @has_access_api
    @expose("/fave_dashboards_by_username/<username>/", methods=["GET"])
    def fave_dashboards_by_username(self, username):
        """This lets us use a user's username to pull favourite dashboards"""
        user = security_manager.find_user(username=username)
        return self.fave_dashboards(user.get_id())

    @api
    @has_access_api
    @expose("/fave_dashboards/<user_id>/", methods=["GET"])
    def fave_dashboards(self, user_id):
        qry = (
            db.session.query(models.Dashboard, models.FavStar.dttm)
            .join(
                models.FavStar,
                and_(
                    models.FavStar.user_id == int(user_id),
                    models.FavStar.class_name == "Dashboard",
                    models.Dashboard.id == models.FavStar.obj_id,
                ),
            )
            .order_by(models.FavStar.dttm.desc())
        )
        payload = []
        for o in qry.all():
            d = {
                "id": o.Dashboard.id,
                "dashboard": o.Dashboard.dashboard_link(),
                "title": o.Dashboard.dashboard_title,
                "url": o.Dashboard.url,
                "dttm": o.dttm,
            }
            if o.Dashboard.created_by:
                user = o.Dashboard.created_by
                d["creator"] = str(user)
                d["creator_url"] = "/superset/profile/{}/".format(user.username)
            payload.append(d)
        return json_success(json.dumps(payload, default=utils.json_int_dttm_ser))

    @api
    @has_access_api
    @expose("/created_dashboards/<user_id>/", methods=["GET"])
    def created_dashboards(self, user_id):
        Dash = models.Dashboard  # noqa
        qry = (
            db.session.query(Dash)
            .filter(or_(Dash.created_by_fk == user_id, Dash.changed_by_fk == user_id))
            .order_by(Dash.changed_on.desc())
        )
        payload = [
            {
                "id": o.id,
                "dashboard": o.dashboard_link(),
                "title": o.dashboard_title,
                "url": o.url,
                "dttm": o.changed_on,
            }
            for o in qry.all()
        ]
        return json_success(json.dumps(payload, default=utils.json_int_dttm_ser))

    @api
    @has_access_api
    @expose("/user_slices", methods=["GET"])
    @expose("/user_slices/<user_id>/", methods=["GET"])
    def user_slices(self, user_id=None):
        """List of slices a user created, or faved"""
        if not user_id:
            user_id = g.user.id
        Slice = models.Slice  # noqa
        FavStar = models.FavStar  # noqa
        qry = (
            db.session.query(Slice, FavStar.dttm)
            .join(
                models.FavStar,
                and_(
                    models.FavStar.user_id == int(user_id),
                    models.FavStar.class_name == "slice",
                    models.Slice.id == models.FavStar.obj_id,
                ),
                isouter=True,
            )
            .filter(
                or_(
                    Slice.created_by_fk == user_id,
                    Slice.changed_by_fk == user_id,
                    FavStar.user_id == user_id,
                )
            )
            .order_by(Slice.slice_name.asc())
        )
        payload = [
            {
                "id": o.Slice.id,
                "title": o.Slice.slice_name,
                "url": o.Slice.slice_url,
                "data": o.Slice.form_data,
                "dttm": o.dttm if o.dttm else o.Slice.changed_on,
                "viz_type": o.Slice.viz_type,
            }
            for o in qry.all()
        ]
        return json_success(json.dumps(payload, default=utils.json_int_dttm_ser))

    @api
    @has_access_api
    @expose("/created_slices", methods=["GET"])
    @expose("/created_slices/<user_id>/", methods=["GET"])
    def created_slices(self, user_id=None):
        """List of slices created by this user"""
        if not user_id:
            user_id = g.user.id
        Slice = models.Slice  # noqa
        qry = (
            db.session.query(Slice)
            .filter(or_(Slice.created_by_fk == user_id, Slice.changed_by_fk == user_id))
            .order_by(Slice.changed_on.desc())
        )
        payload = [
            {
                "id": o.id,
                "title": o.slice_name,
                "url": o.slice_url,
                "dttm": o.changed_on,
                "viz_type": o.viz_type,
            }
            for o in qry.all()
        ]
        return json_success(json.dumps(payload, default=utils.json_int_dttm_ser))

    @api
    @has_access_api
    @expose("/fave_slices", methods=["GET"])
    @expose("/fave_slices/<user_id>/", methods=["GET"])
    def fave_slices(self, user_id=None):
        """Favorite slices for a user"""
        if not user_id:
            user_id = g.user.id
        qry = (
            db.session.query(models.Slice, models.FavStar.dttm)
            .join(
                models.FavStar,
                and_(
                    models.FavStar.user_id == int(user_id),
                    models.FavStar.class_name == "slice",
                    models.Slice.id == models.FavStar.obj_id,
                ),
            )
            .order_by(models.FavStar.dttm.desc())
        )
        payload = []
        for o in qry.all():
            d = {
                "id": o.Slice.id,
                "title": o.Slice.slice_name,
                "url": o.Slice.slice_url,
                "dttm": o.dttm,
                "viz_type": o.Slice.viz_type,
            }
            if o.Slice.created_by:
                user = o.Slice.created_by
                d["creator"] = str(user)
                d["creator_url"] = "/superset/profile/{}/".format(user.username)
            payload.append(d)
        return json_success(json.dumps(payload, default=utils.json_int_dttm_ser))

    @api
    @has_access_api
    @expose("/warm_up_cache/", methods=["GET"])
    def warm_up_cache(self):
        """Warms up the cache for the slice or table.

        Note for slices a force refresh occurs.
        """
        slices = None
        session = db.session()
        slice_id = request.args.get("slice_id")
        table_name = request.args.get("table_name")
        db_name = request.args.get("db_name")

        if not slice_id and not (table_name and db_name):
            return json_error_response(
                __(
                    "Malformed request. slice_id or table_name and db_name "
                    "arguments are expected"
                ),
                status=400,
            )
        if slice_id:
            slices = session.query(models.Slice).filter_by(id=slice_id).all()
            if not slices:
                return json_error_response(
                    __("Chart %(id)s not found", id=slice_id), status=404
                )
        elif table_name and db_name:
            SqlaTable = ConnectorRegistry.sources["table"]
            table = (
                session.query(SqlaTable)
                .join(models.Database)
                .filter(
                    models.Database.database_name == db_name
                    or SqlaTable.table_name == table_name
                )
            ).first()
            if not table:
                return json_error_response(
                    __(
                        "Table %(t)s wasn't found in the database %(d)s",
                        t=table_name,
                        s=db_name,
                    ),
                    status=404,
                )
            slices = (
                session.query(models.Slice)
                .filter_by(datasource_id=table.id, datasource_type=table.type)
                .all()
            )

        for slc in slices:
            try:
                form_data = get_form_data(slc.id, use_slice_data=True)[0]
                obj = get_viz(
                    datasource_type=slc.datasource.type,
                    datasource_id=slc.datasource.id,
                    form_data=form_data,
                    force=True,
                )
                obj.get_json()
            except Exception as e:
                return json_error_response(utils.error_msg_from_exception(e))
        return json_success(
            json.dumps(
                [{"slice_id": slc.id, "slice_name": slc.slice_name} for slc in slices]
            )
        )

    @has_access_api
    @expose("/favstar/<class_name>/<obj_id>/<action>/")
    def favstar(self, class_name, obj_id, action):
        """Toggle favorite stars on Slices and Dashboard"""
        session = db.session()
        FavStar = models.FavStar  # noqa
        count = 0
        favs = (
            session.query(FavStar)
            .filter_by(class_name=class_name, obj_id=obj_id, user_id=g.user.get_id())
            .all()
        )
        if action == "select":
            if not favs:
                session.add(
                    FavStar(
                        class_name=class_name,
                        obj_id=obj_id,
                        user_id=g.user.get_id(),
                        dttm=datetime.now(),
                    )
                )
            count = 1
        elif action == "unselect":
            for fav in favs:
                session.delete(fav)
        else:
            count = len(favs)
        session.commit()
        return json_success(json.dumps({"count": count}))

    @api
    @has_access_api
    @expose("/dashboard/<dashboard_id>/published/", methods=("GET", "POST"))
    def publish(self, dashboard_id):
        """Gets and toggles published status on dashboards"""
        session = db.session()
        Dashboard = models.Dashboard  # noqa
        Role = ab_models.Role
        dash = (
            session.query(Dashboard).filter(Dashboard.id == dashboard_id).one_or_none()
        )
        admin_role = session.query(Role).filter(Role.name == "Admin").one_or_none()

        if request.method == "GET":
            if dash:
                return json_success(json.dumps({"published": dash.published}))
            else:
                return json_error_response(
                    "ERROR: cannot find dashboard {0}".format(dashboard_id), status=404
                )

        else:
            edit_perm = is_owner(dash, g.user) or admin_role in get_user_roles()
            if not edit_perm:
                return json_error_response(
                    'ERROR: "{0}" cannot alter dashboard "{1}"'.format(
                        g.user.username, dash.dashboard_title
                    ),
                    status=403,
                )

            dash.published = str(request.form["published"]).lower() == "true"
            session.commit()
            return json_success(json.dumps({"published": dash.published}))

    @has_access
    @expose("/dashboard/<dashboard_id>/")
    def dashboard(self, dashboard_id):
        """Server side rendering for a dashboard"""
        session = db.session()
        qry = session.query(models.Dashboard)
        if dashboard_id.isdigit():
            qry = qry.filter_by(id=int(dashboard_id))
        else:
            qry = qry.filter_by(slug=dashboard_id)

        dash = qry.one_or_none()
        if not dash:
            abort(404)
        datasources = set()
        for slc in dash.slices:
            datasource = slc.datasource
            if datasource:
                datasources.add(datasource)

        if config.get("ENABLE_ACCESS_REQUEST"):
            for datasource in datasources:
                if datasource and not security_manager.datasource_access(datasource):
                    flash(
                        __(
                            security_manager.get_datasource_access_error_msg(datasource)
                        ),
                        "danger",
                    )
                    return redirect(
                        "superset/request_access/?" f"dashboard_id={dash.id}&"
                    )

        dash_edit_perm = check_ownership(
            dash, raise_if_false=False
        ) and security_manager.can_access("can_save_dash", "Superset")
        dash_save_perm = security_manager.can_access("can_save_dash", "Superset")
        superset_can_explore = security_manager.can_access("can_explore", "Superset")
        superset_can_csv = security_manager.can_access("can_csv", "Superset")
        slice_can_edit = security_manager.can_access("can_edit", "SliceModelView")

        standalone_mode = request.args.get("standalone") == "true"
        edit_mode = request.args.get("edit") == "true"

        # Hack to log the dashboard_id properly, even when getting a slug
        @event_logger.log_this
        def dashboard(**kwargs):  # noqa
            pass

        dashboard(
            dashboard_id=dash.id,
            dashboard_version="v2",
            dash_edit_perm=dash_edit_perm,
            edit_mode=edit_mode,
        )

        dashboard_data = dash.data
        dashboard_data.update(
            {
                "standalone_mode": standalone_mode,
                "dash_save_perm": dash_save_perm,
                "dash_edit_perm": dash_edit_perm,
                "superset_can_explore": superset_can_explore,
                "superset_can_csv": superset_can_csv,
                "slice_can_edit": slice_can_edit,
            }
        )

        bootstrap_data = {
            "user_id": g.user.get_id(),
            "dashboard_data": dashboard_data,
            "datasources": {ds.uid: ds.data for ds in datasources},
            "common": self.common_bootstrap_payload(),
            "editMode": edit_mode,
        }

        if request.args.get("json") == "true":
            return json_success(json.dumps(bootstrap_data))

        return self.render_template(
            "superset/dashboard.html",
            entry="dashboard",
            standalone_mode=standalone_mode,
            title=dash.dashboard_title,
            bootstrap_data=json.dumps(bootstrap_data),
        )

    @api
    @event_logger.log_this
    @expose("/log/", methods=["POST"])
    def log(self):
        return Response(status=200)

    @has_access
    @expose("/sync_druid/", methods=["POST"])
    @event_logger.log_this
    def sync_druid_source(self):
        """Syncs the druid datasource in main db with the provided config.

        The endpoint takes 3 arguments:
            user - user name to perform the operation as
            cluster - name of the druid cluster
            config - configuration stored in json that contains:
                name: druid datasource name
                dimensions: list of the dimensions, they become druid columns
                    with the type STRING
                metrics_spec: list of metrics (dictionary). Metric consists of
                    2 attributes: type and name. Type can be count,
                    etc. `count` type is stored internally as longSum
                    other fields will be ignored.

            Example: {
                'name': 'test_click',
                'metrics_spec': [{'type': 'count', 'name': 'count'}],
                'dimensions': ['affiliate_id', 'campaign', 'first_seen']
            }
        """
        payload = request.get_json(force=True)
        druid_config = payload["config"]
        user_name = payload["user"]
        cluster_name = payload["cluster"]

        user = security_manager.find_user(username=user_name)
        DruidDatasource = ConnectorRegistry.sources["druid"]
        DruidCluster = DruidDatasource.cluster_class
        if not user:
            err_msg = __(
                "Can't find User '%(name)s', please ask your admin " "to create one.",
                name=user_name,
            )
            logging.error(err_msg)
            return json_error_response(err_msg)
        cluster = (
            db.session.query(DruidCluster).filter_by(cluster_name=cluster_name).first()
        )
        if not cluster:
            err_msg = __(
                "Can't find DruidCluster with cluster_name = " "'%(name)s'",
                name=cluster_name,
            )
            logging.error(err_msg)
            return json_error_response(err_msg)
        try:
            DruidDatasource.sync_to_db_from_config(druid_config, user, cluster)
        except Exception as e:
            logging.exception(utils.error_msg_from_exception(e))
            return json_error_response(utils.error_msg_from_exception(e))
        return Response(status=201)

    @has_access
    @expose("/sqllab_viz/", methods=["POST"])
    @event_logger.log_this
    def sqllab_viz(self):
        SqlaTable = ConnectorRegistry.sources["table"]
        data = json.loads(request.form.get("data"))
        table_name = data.get("datasourceName")
        table = db.session.query(SqlaTable).filter_by(table_name=table_name).first()
        if not table:
            table = SqlaTable(table_name=table_name)
        table.database_id = data.get("dbId")
        table.schema = data.get("schema")
        table.template_params = data.get("templateParams")
        table.is_sqllab_view = True
        q = ParsedQuery(data.get("sql"))
        table.sql = q.stripped()
        db.session.add(table)
        cols = []
        for config in data.get("columns"):
            column_name = config.get("name")
            SqlaTable = ConnectorRegistry.sources["table"]
            TableColumn = SqlaTable.column_class
            SqlMetric = SqlaTable.metric_class
            col = TableColumn(
                column_name=column_name,
                filterable=True,
                groupby=True,
                is_dttm=config.get("is_date", False),
                type=config.get("type", False),
            )
            cols.append(col)

        table.columns = cols
        table.metrics = [SqlMetric(metric_name="count", expression="count(*)")]
        db.session.commit()
        return json_success(json.dumps({"table_id": table.id}))

    @has_access
    @expose("/table/<database_id>/<table_name>/<schema>/")
    @event_logger.log_this
    def table(self, database_id, table_name, schema):
        schema = utils.parse_js_uri_path_item(schema, eval_undefined=True)
        table_name = utils.parse_js_uri_path_item(table_name)
        mydb = db.session.query(models.Database).filter_by(id=database_id).one()
        payload_columns = []
        indexes = []
        primary_key = []
        foreign_keys = []
        try:
            columns = mydb.get_columns(table_name, schema)
            indexes = mydb.get_indexes(table_name, schema)
            primary_key = mydb.get_pk_constraint(table_name, schema)
            foreign_keys = mydb.get_foreign_keys(table_name, schema)
        except Exception as e:
            return json_error_response(utils.error_msg_from_exception(e))
        keys = []
        if primary_key and primary_key.get("constrained_columns"):
            primary_key["column_names"] = primary_key.pop("constrained_columns")
            primary_key["type"] = "pk"
            keys += [primary_key]
        for fk in foreign_keys:
            fk["column_names"] = fk.pop("constrained_columns")
            fk["type"] = "fk"
        keys += foreign_keys
        for idx in indexes:
            idx["type"] = "index"
        keys += indexes

        for col in columns:
            dtype = ""
            try:
                dtype = "{}".format(col["type"])
            except Exception:
                # sqla.types.JSON __str__ has a bug, so using __class__.
                dtype = col["type"].__class__.__name__
                pass
            payload_columns.append(
                {
                    "name": col["name"],
                    "type": dtype.split("(")[0] if "(" in dtype else dtype,
                    "longType": dtype,
                    "keys": [k for k in keys if col["name"] in k.get("column_names")],
                }
            )
        tbl = {
            "name": table_name,
            "columns": payload_columns,
            "selectStar": mydb.select_star(
                table_name,
                schema=schema,
                show_cols=True,
                indent=True,
                cols=columns,
                latest_partition=True,
            ),
            "primaryKey": primary_key,
            "foreignKeys": foreign_keys,
            "indexes": keys,
        }
        return json_success(json.dumps(tbl))

    @has_access
    @expose("/extra_table_metadata/<database_id>/<table_name>/<schema>/")
    @event_logger.log_this
    def extra_table_metadata(self, database_id, table_name, schema):
        schema = utils.parse_js_uri_path_item(schema, eval_undefined=True)
        table_name = utils.parse_js_uri_path_item(table_name)
        mydb = db.session.query(models.Database).filter_by(id=database_id).one()
        payload = mydb.db_engine_spec.extra_table_metadata(mydb, table_name, schema)
        return json_success(json.dumps(payload))

    @has_access
    @expose("/select_star/<database_id>/<table_name>")
    @expose("/select_star/<database_id>/<table_name>/<schema>")
    @event_logger.log_this
    def select_star(self, database_id, table_name, schema=None):
        mydb = db.session.query(models.Database).filter_by(id=database_id).first()
        schema = utils.parse_js_uri_path_item(schema, eval_undefined=True)
        table_name = utils.parse_js_uri_path_item(table_name)
        return json_success(
            mydb.select_star(table_name, schema, latest_partition=True, show_cols=True)
        )

    @expose("/theme/")
    def theme(self):
        return self.render_template("superset/theme.html")

    @has_access_api
    @expose("/cached_key/<key>/")
    @event_logger.log_this
    def cached_key(self, key):
        """Returns a key from the cache"""
        resp = cache.get(key)
        if resp:
            return resp
        return "nope"

    @has_access_api
    @expose("/cache_key_exist/<key>/")
    @event_logger.log_this
    def cache_key_exist(self, key):
        """Returns if a key from cache exist"""
        key_exist = True if cache.get(key) else False
        status = 200 if key_exist else 404
        return json_success(json.dumps({"key_exist": key_exist}), status=status)

    @has_access_api
    @expose("/results/<key>/")
    @event_logger.log_this
    def results(self, key):
        """Serves a key off of the results backend"""
        if not results_backend:
            return json_error_response("Results backend isn't configured")

        read_from_results_backend_start = now_as_float()
        blob = results_backend.get(key)
        stats_logger.timing(
            "sqllab.query.results_backend_read",
            now_as_float() - read_from_results_backend_start,
        )
        if not blob:
            return json_error_response(
                "Data could not be retrieved. " "You may want to re-run the query.",
                status=410,
            )

        query = db.session.query(Query).filter_by(results_key=key).one()
        rejected_tables = security_manager.rejected_tables(
            query.sql, query.database, query.schema
        )
        if rejected_tables:
            return json_error_response(
                security_manager.get_table_access_error_msg(
                    "{}".format(rejected_tables)
                ),
                status=403,
            )

        payload = utils.zlib_decompress_to_string(blob)
        payload_json = json.loads(payload)

        return json_success(
            json.dumps(
                apply_display_max_row_limit(payload_json),
                default=utils.json_iso_dttm_ser,
                ignore_nan=True,
            )
        )

    @has_access_api
    @expose("/stop_query/", methods=["POST"])
    @event_logger.log_this
    def stop_query(self):
        client_id = request.form.get("client_id")
        try:
            query = db.session.query(Query).filter_by(client_id=client_id).one()
            query.status = QueryStatus.STOPPED
            db.session.commit()
        except Exception:
            pass
        return self.json_response("OK")

    @has_access_api
    @expose("/validate_sql_json/", methods=["POST", "GET"])
    @event_logger.log_this
    def validate_sql_json(self):
        """Validates that arbitrary sql is acceptable for the given database.
        Returns a list of error/warning annotations as json.
        """
        sql = request.form.get("sql")
        database_id = request.form.get("database_id")
        schema = request.form.get("schema") or None
        template_params = json.loads(request.form.get("templateParams") or "{}")

        if len(template_params) > 0:
            # TODO: factor the Database object out of template rendering
            #       or provide it as mydb so we can render template params
            #       without having to also persist a Query ORM object.
            return json_error_response(
                "SQL validation does not support template parameters", status=400
            )

        session = db.session()
        mydb = session.query(models.Database).filter_by(id=database_id).first()
        if not mydb:
            json_error_response(
                "Database with id {} is missing.".format(database_id), status=400
            )

        spec = mydb.db_engine_spec
        validators_by_engine = get_feature_flags().get("SQL_VALIDATORS_BY_ENGINE")
        if not validators_by_engine or spec.engine not in validators_by_engine:
            return json_error_response(
                "no SQL validator is configured for {}".format(spec.engine), status=400
            )
        validator_name = validators_by_engine[spec.engine]
        validator = get_validator_by_name(validator_name)
        if not validator:
            return json_error_response(
                "No validator named {} found (configured for the {} engine)".format(
                    validator_name, spec.engine
                )
            )

        try:
            timeout = config.get("SQLLAB_VALIDATION_TIMEOUT")
            timeout_msg = f"The query exceeded the {timeout} seconds timeout."
            with utils.timeout(seconds=timeout, error_message=timeout_msg):
                errors = validator.validate(sql, schema, mydb)
            payload = json.dumps(
                [err.to_dict() for err in errors],
                default=utils.pessimistic_json_iso_dttm_ser,
                ignore_nan=True,
                encoding=None,
            )
            return json_success(payload)
        except Exception as e:
            logging.exception(e)
            msg = _(
                f"{validator.name} was unable to check your query.\nPlease "
                "make sure that any services it depends on are available\n"
                f"Exception: {e}"
            )
            return json_error_response(f"{msg}")

    @has_access_api
    @expose("/sql_json/", methods=["POST", "GET"])
    @event_logger.log_this
    def sql_json(self):
        """Runs arbitrary sql and returns and json"""
        async_ = request.form.get("runAsync") == "true"
        sql = request.form.get("sql")
        database_id = request.form.get("database_id")
        schema = request.form.get("schema") or None
        template_params = json.loads(request.form.get("templateParams") or "{}")
        limit = int(request.form.get("queryLimit", 0))
        if limit < 0:
            logging.warning(
                "Invalid limit of {} specified. Defaulting to max limit.".format(limit)
            )
            limit = 0
        limit = limit or app.config.get("SQL_MAX_ROW")

        session = db.session()
        mydb = session.query(models.Database).filter_by(id=database_id).first()

        if not mydb:
            json_error_response("Database with id {} is missing.".format(database_id))

        rejected_tables = security_manager.rejected_tables(sql, mydb, schema)
        if rejected_tables:
            return json_error_response(
                security_manager.get_table_access_error_msg(rejected_tables),
                link=security_manager.get_table_access_link(rejected_tables),
                status=403,
            )
        session.commit()

        select_as_cta = request.form.get("select_as_cta") == "true"
        tmp_table_name = request.form.get("tmp_table_name")
        if select_as_cta and mydb.force_ctas_schema:
            tmp_table_name = "{}.{}".format(mydb.force_ctas_schema, tmp_table_name)

        client_id = request.form.get("client_id") or utils.shortid()[:10]
        query = Query(
            database_id=int(database_id),
            sql=sql,
            schema=schema,
            select_as_cta=select_as_cta,
            start_time=now_as_float(),
            tab_name=request.form.get("tab"),
            status=QueryStatus.PENDING if async_ else QueryStatus.RUNNING,
            sql_editor_id=request.form.get("sql_editor_id"),
            tmp_table_name=tmp_table_name,
            user_id=g.user.get_id() if g.user else None,
            client_id=client_id,
        )
        session.add(query)
        session.flush()
        query_id = query.id
        session.commit()  # shouldn't be necessary
        if not query_id:
            raise Exception(_("Query record was not created as expected."))
        logging.info("Triggering query_id: {}".format(query_id))

        try:
            template_processor = get_template_processor(
                database=query.database, query=query
            )
            rendered_query = template_processor.process_template(
                query.sql, **template_params
            )
        except Exception as e:
            return json_error_response(
                "Template rendering failed: {}".format(
                    utils.error_msg_from_exception(e)
                )
            )

        # set LIMIT after template processing
        limits = [mydb.db_engine_spec.get_limit_from_sql(rendered_query), limit]
        query.limit = min(lim for lim in limits if lim is not None)

        # Async request.
        if async_:
            logging.info("Running query on a Celery worker")
            # Ignore the celery future object and the request may time out.
            try:
                sql_lab.get_sql_results.delay(
                    query_id,
                    rendered_query,
                    return_results=False,
                    store_results=not query.select_as_cta,
                    user_name=g.user.username if g.user else None,
                    start_time=now_as_float(),
                )
            except Exception as e:
                logging.exception(e)
                msg = _(
                    "Failed to start remote query on a worker. "
                    "Tell your administrator to verify the availability of "
                    "the message queue."
                )
                query.status = QueryStatus.FAILED
                query.error_message = msg
                session.commit()
                return json_error_response("{}".format(msg))

            resp = json_success(
                json.dumps(
                    {"query": query.to_dict()},
                    default=utils.json_int_dttm_ser,
                    ignore_nan=True,
                ),
                status=202,
            )
            session.commit()
            return resp

        # Sync request.
        try:
            timeout = config.get("SQLLAB_TIMEOUT")
            timeout_msg = f"The query exceeded the {timeout} seconds timeout."
            with utils.timeout(seconds=timeout, error_message=timeout_msg):
                # pylint: disable=no-value-for-parameter
                data = sql_lab.get_sql_results(
                    query_id,
                    rendered_query,
                    return_results=True,
                    user_name=g.user.username if g.user else None,
                )

            payload = json.dumps(
                apply_display_max_row_limit(data),
                default=utils.pessimistic_json_iso_dttm_ser,
                ignore_nan=True,
                encoding=None,
            )
        except Exception as e:
            logging.exception(e)
            return json_error_response("{}".format(e))
        if data.get("status") == QueryStatus.FAILED:
            return json_error_response(payload=data)
        return json_success(payload)

    @has_access
    @expose("/csv/<client_id>")
    @event_logger.log_this
    def csv(self, client_id):
        """Download the query results as csv."""
        logging.info("Exporting CSV file [{}]".format(client_id))
        query = db.session.query(Query).filter_by(client_id=client_id).one()

        rejected_tables = security_manager.rejected_tables(
            query.sql, query.database, query.schema
        )
        if rejected_tables:
            flash(
                security_manager.get_table_access_error_msg(
                    "{}".format(rejected_tables)
                )
            )
            return redirect("/")
        blob = None
        if results_backend and query.results_key:
            logging.info(
                "Fetching CSV from results backend " "[{}]".format(query.results_key)
            )
            blob = results_backend.get(query.results_key)
        if blob:
            logging.info("Decompressing")
            json_payload = utils.zlib_decompress_to_string(blob)
            obj = json.loads(json_payload)
            columns = [c["name"] for c in obj["columns"]]
            df = pd.DataFrame.from_records(obj["data"], columns=columns)
            logging.info("Using pandas to convert to CSV")
            csv = df.to_csv(index=False, **config.get("CSV_EXPORT"))
        else:
            logging.info("Running a query to turn into CSV")
            sql = query.select_sql or query.executed_sql
            df = query.database.get_df(sql, query.schema)
            # TODO(bkyryliuk): add compression=gzip for big files.
            csv = df.to_csv(index=False, **config.get("CSV_EXPORT"))
        response = Response(csv, mimetype="text/csv")
        response.headers[
            "Content-Disposition"
        ] = f"attachment; filename={query.name}.csv"
        logging.info("Ready to return response")
        return response

    @api
    @handle_api_exception
    @has_access
    @expose("/fetch_datasource_metadata")
    @event_logger.log_this
    def fetch_datasource_metadata(self):
        datasource_id, datasource_type = request.args.get("datasourceKey").split("__")
        datasource = ConnectorRegistry.get_datasource(
            datasource_type, datasource_id, db.session
        )
        # Check if datasource exists
        if not datasource:
            return json_error_response(DATASOURCE_MISSING_ERR)

        # Check permission for datasource
        security_manager.assert_datasource_permission(datasource)
        return json_success(json.dumps(datasource.data))

    @has_access_api
    @expose("/queries/<last_updated_ms>")
    def queries(self, last_updated_ms):
        """Get the updated queries."""
        stats_logger.incr("queries")
        if not g.user.get_id():
            return json_error_response(
                "Please login to access the queries.", status=403
            )

        # Unix time, milliseconds.
        last_updated_ms_int = int(float(last_updated_ms)) if last_updated_ms else 0

        # UTC date time, same that is stored in the DB.
        last_updated_dt = utils.EPOCH + timedelta(seconds=last_updated_ms_int / 1000)

        sql_queries = (
            db.session.query(Query)
            .filter(
                Query.user_id == g.user.get_id(), Query.changed_on >= last_updated_dt
            )
            .all()
        )
        dict_queries = {q.client_id: q.to_dict() for q in sql_queries}
        return json_success(json.dumps(dict_queries, default=utils.json_int_dttm_ser))

    @has_access
    @expose("/search_queries")
    @event_logger.log_this
    def search_queries(self) -> Response:
        """
        Search for previously run sqllab queries. Used for Sqllab Query Search
        page /superset/sqllab#search.

        Custom permission can_only_search_queries_owned restricts queries
        to only queries run by current user.

        :returns: Response with list of sql query dicts
        """
        query = db.session.query(Query)
        if security_manager.can_only_access_owned_queries():
            search_user_id = g.user.get_user_id()
        else:
            search_user_id = request.args.get("user_id")
        database_id = request.args.get("database_id")
        search_text = request.args.get("search_text")
        status = request.args.get("status")
        # From and To time stamp should be Epoch timestamp in seconds
        from_time = request.args.get("from")
        to_time = request.args.get("to")

        if search_user_id:
            # Filter on user_id
            query = query.filter(Query.user_id == search_user_id)

        if database_id:
            # Filter on db Id
            query = query.filter(Query.database_id == database_id)

        if status:
            # Filter on status
            query = query.filter(Query.status == status)

        if search_text:
            # Filter on search text
            query = query.filter(Query.sql.like("%{}%".format(search_text)))

        if from_time:
            query = query.filter(Query.start_time > int(from_time))

        if to_time:
            query = query.filter(Query.start_time < int(to_time))

        query_limit = config.get("QUERY_SEARCH_LIMIT", 1000)
        sql_queries = query.order_by(Query.start_time.asc()).limit(query_limit).all()

        dict_queries = [q.to_dict() for q in sql_queries]

        return Response(
            json.dumps(dict_queries, default=utils.json_int_dttm_ser),
            status=200,
            mimetype="application/json",
        )

    @app.errorhandler(500)
    def show_traceback(self):
        return (
            render_template("solar/500_error.html"),
            500,
        )
        # return (
        #     render_template("superset/traceback.html", error_msg=get_error_msg()),
        #     500,
        # )

    @app.errorhandler(404)
    def page_not_found(self):
        return (
            render_template("solar/404_error.html"),
            404,
        )


    @expose("/welcome")
    def welcome(self):
        """Personalized welcome page"""

        if not g.user or not g.user.get_id():
            return redirect(appbuilder.get_url_for_login)

        entry_point = 'solarBI'

        datasource_id = ''
        for role in g.user.roles:

            for permission in role.permissions:
                if permission.permission.name == 'datasource_access':
                    datasource_id = \
                        permission.view_menu.name.split(':')[1].replace(')', '')
                    break

        welcome_dashboard_id = (
            db.session.query(UserAttribute.welcome_dashboard_id)
            .filter_by(user_id=g.user.get_id())
            .scalar()
        )
        if welcome_dashboard_id:
            return self.dashboard(str(welcome_dashboard_id))

        payload = {
            'user': bootstrap_user_data(g.user),
            'common': self.common_bootstrap_payload(),
            'datasource_id': datasource_id,
            'datasource_type': 'table',
        }

        return self.render_template(
            'superset/basic.html',
            entry=entry_point,
            title='Superset',
            bootstrap_data=json.dumps(payload, default=utils.json_iso_dttm_ser),
        )

    def get_form_data_in_solarbi_slices(self, slice_id=None, use_slice_data=False):
        form_data = {}
        post_data = request.form.get("form_data")
        request_args_data = request.args.get("form_data")
        # Supporting POST
        if post_data:
            form_data.update(json.loads(post_data))
        # request params can overwrite post body
        if request_args_data:
            form_data.update(json.loads(request_args_data))

        url_id = request.args.get("r")
        if url_id:
            saved_url = db.session.query(models.Url).filter_by(id=url_id).first()
            if saved_url:
                url_str = parse.unquote_plus(
                    saved_url.url.split("?")[1][10:], encoding="utf-8", errors=None
                )
                url_form_data = json.loads(url_str)
                # allow form_date in request override saved url
                url_form_data.update(form_data)
                form_data = url_form_data

        form_data = {
            k: v for k, v in form_data.items() if k not in FORM_DATA_KEY_BLACKLIST
        }

        # When a slice_id is present, load from DB and override
        # the form_data from the DB with the other form_data provided
        slice_id = form_data.get("slice_id") or slice_id
        slc = None

        # Check if form data only contains slice_id
        contains_only_slc_id = not any(key != "slice_id" for key in form_data)

        # Include the slice_form_data if request from explore or slice calls
        # or if form_data only contains slice_id
        if slice_id and (use_slice_data or contains_only_slc_id):
            slc = db.session.query(models.SolarBISlice).filter_by(id=slice_id).one_or_none()
            if slc:
                slice_form_data = slc.form_data.copy()
                slice_form_data.update(form_data)
                form_data = slice_form_data

        update_time_range(form_data)

        return form_data, slc

    def save_or_overwrite_solarbislice(
        self,
        args,
        slc,
        slice_add_perm,
        slice_overwrite_perm,
        slice_download_perm,
        datasource_id,
        datasource_type,
        datasource_name,
        query_id=None,
        start_date=None,
        end_date=None,
        data_type=None,
        resolution=None,
    ):
        """Save or overwrite a slice"""
        slice_name = args.get("slice_name")
        action = args.get("action")
        form_data = get_form_data()[0]

        if action in ("saveas"):
            if "slice_id" in form_data:
                form_data.pop("slice_id")  # don't save old slice_id
            slc = models.SolarBISlice(owners=[g.user] if g.user else [])

        slc.team_id = get_session_team(self.appbuilder.sm, g.user.id)[0]
        slc.params = json.dumps(form_data, indent=2, sort_keys=True)
        slc.datasource_name = datasource_name
        slc.viz_type = form_data["viz_type"]
        slc.datasource_type = datasource_type
        slc.datasource_id = datasource_id
        slc.slice_name = slice_name
        slc.query_status = 'N/A'
        if query_id:
            slc.query_status = 'running'
            slc.paid = True
            slc.valid_date = datetime.now() + timedelta(hours=24*31*12*99)
            slc.query_id = query_id
        if start_date:
            slc.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            slc.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        if data_type:
            slc.data_type = data_type
        if resolution:
            slc.resolution = resolution

        if action in ("saveas") and slice_add_perm:
            self.save_slice(slc, paid=slc.paid)
        elif action == "overwrite" and slice_overwrite_perm:
            self.overwrite_slice(slc)

        # Adding slice to a dashboard if requested
        dash = None

        response = {
            "can_add": slice_add_perm,
            "can_download": slice_download_perm,
            "can_overwrite": is_owner(slc, g.user),
            "form_data": slc.form_data,
            "slice": slc.data,
            "dashboard_id": dash.id if dash else None,
        }


        if request.args.get("goto_dash") == "true":
            response.update({"dashboard": dash.url})

        return json_success(json.dumps(response))

    @expose('/solar/', methods=('GET', 'POST'))
    def solar(self):
        if not g.user or not g.user.get_id():
            return redirect(appbuilder.get_url_for_login)

        user_id = g.user.get_id() if g.user else None
        # form_data, slc = self.get_form_data(use_slice_data=True)
        form_data, slc = self.get_form_data_in_solarbi_slices(use_slice_data=True)

        datasource_id, datasource_type = get_datasource_info(
            form_data['datasource_id']
            if 'datasource_id' in form_data.keys() else None,
            form_data['datasource_type']
            if 'datasource_type' in form_data.keys() else None,
            form_data)

        error_redirect = '/solar/list'
        datasource = ConnectorRegistry.get_datasource(
            datasource_type, datasource_id, db.session)
        if not datasource:
            flash(DATASOURCE_MISSING_ERR, 'danger')
            return redirect(error_redirect)

        if config.get('ENABLE_ACCESS_REQUEST') and (
                not security_manager.datasource_access(datasource)
        ):
            flash(
                __(security_manager.get_datasource_access_error_msg(datasource)),
                'danger')
            return redirect(
                'superset/request_access/?'
                'datasource_type={datasource_type}&'
                'datasource_id={datasource_id}&'
                ''.format(**locals()))

        viz_type = form_data.get('viz_type')
        if not viz_type and datasource.default_endpoint:
            return redirect(datasource.default_endpoint)

        # slc perms
        slice_add_perm = security_manager.can_access('can_add', 'SolarBIModelView')
        slice_overwrite_perm = is_owner(slc, g.user)
        slice_download_perm = security_manager.can_access(
            'can_download', 'SolarBIModelView')

        form_data['datasource'] = str(datasource_id) + '__' + datasource_type

        # merge request url params
        if request.method == 'GET':
            utils.merge_request_params(form_data, request.args)

        # handle save or overwrite
        action = request.args.get('action')

        if action == 'overwrite' and not slice_overwrite_perm:
            return json_error_response(
                _('You don\'t have the rights to ') + _('alter this ') + _('chart'),
                status=400)

        if action == 'saveas' and not slice_add_perm:
            return json_error_response(
                _('You don\'t have the rights to ') + _('create a ') + _('chart'),
                status=400)

        if action in ('saveas', 'overwrite'):

            # Log to mixpanel
            log_to_mp(g.user, get_session_team(self.appbuilder.sm, g.user.id)[1], 'save search', {
                "name": form_data['requestParams']['slice_name']
            })

            return self.save_or_overwrite_solarbislice(
                request.args,
                slc, slice_add_perm,
                slice_overwrite_perm,
                slice_download_perm,
                datasource_id,
                datasource_type,
                datasource.name)

        standalone = request.args.get('standalone') == 'true'
        team = self.appbuilder.get_session.query(Team).filter_by(id=session['team_id']).first()
        subscription = self.appbuilder.sm.get_subscription(team_id=team.id)

        # Count the subscription remaining days
        remain_days = -1
        if subscription.end_time:
            current_datetime = datetime.utcnow()
            end_datetime = datetime.utcfromtimestamp(subscription.end_time)
            remain_days = (end_datetime - current_datetime).days

            # If has passed 14 days of end time, revert customer plan to free
            if remain_days <= -14:
                self.revert_to_free(team)

                # Remove credit card to force update cc for next time
                team.stripe_pm_id = None

        # Check if the team can trial
        can_trial = False
        for team_role in g.user.team_role:
            if team_role.team.id == team.id and team_role.role.name == 'team_owner':
                can_trial = True
        can_trial = can_trial and not g.user.trial_used
        bootstrap_data = {
            'can_add': slice_add_perm,
            'can_download': slice_download_perm,
            'can_overwrite': slice_overwrite_perm,
            'form_data': form_data,
            'datasource_id': datasource_id,
            'datasource_type': datasource_type,
            'slice': slc.data if slc else None,
            'standalone': standalone,
            'user_id': user_id,
            'forced_height': request.args.get('height'),
            'common': self.common_bootstrap_payload(),
            'remain_count': subscription.remain_count,
            'remain_days': remain_days,
            'plan_id': subscription.plan,
            'can_trial': can_trial,
            'saved_queries': [],
        }
        table_name = datasource.table_name \
            if datasource_type == 'table' \
            else datasource.datasource_name
        if slc:
            title = slc.slice_name
        else:
            title = _('Explore - %(table)s', table=table_name)

        is_solar = False

        for role in g.user.roles:
            if role.name == 'Admin':
                is_solar = False
                break
            if role.name == 'solar_default' or role.name == 'team_owner':
                is_solar = True

        return self.render_template(
            'solar/basic.html',
            entry='solarBI',
            title=title,
            bootstrap_data=json.dumps(bootstrap_data),
            standalone_mode=standalone,
            is_solar=is_solar,
        )

    def revert_to_free(self, team):
        try:
            free_plan = self.appbuilder.get_session.query(Plan).filter_by(id=1).first()
            team_sub = self.appbuilder.sm.get_subscription(team_id=team.id)
            if team_sub is None:
                raise Exception('team subscription not found')
            logging.info('Downgrading stripe plan to free.')
            stripe_sub = stripe.Subscription.create(customer=team.stripe_user_id, items=[{
                'plan': free_plan.stripe_id,
                'quantity': '1',
            }])
            logging.info('Old subscription removed and free subscription created')
            logging.info(stripe_sub)
            team_sub.plan = free_plan.id
            team_sub.end_time = stripe_sub['current_period_end']
            team_sub.remain_count = 0
            team = self.appbuilder.sm.find_team(team_id=team_sub.team)
            log_to_mp(None, team.team_name, 'revert to free after 14 days', {})

            self.appbuilder.get_session.commit()
        except Exception as e:
            self.appbuilder.get_session.rollback()
            logging.warning(e)

    @has_access
    @expose("/profile/<username>/")
    def profile(self, username):
        """User profile page"""
        if not username and g.user:
            username = g.user.username

        user = (
            db.session.query(ab_models.User).filter_by(username=username).one_or_none()
        )
        if not user:
            abort(404, description=f"User: {username} does not exist.")

        payload = {
            "user": bootstrap_user_data(user, include_perms=True),
            "common": self.common_bootstrap_payload(),
        }

        return self.render_template(
            "superset/basic.html",
            title=_("%(user)s's profile", user=username),
            entry="profile",
            bootstrap_data=json.dumps(payload, default=utils.json_iso_dttm_ser),
        )

    @has_access
    @expose("/sqllab")
    def sqllab(self):
        """SQL Editor"""
        d = {
            "defaultDbId": config.get("SQLLAB_DEFAULT_DBID"),
            "common": self.common_bootstrap_payload(),
        }

        return self.render_template(
            "superset/basic.html",
            entry="sqllab",
            bootstrap_data=json.dumps(d, default=utils.json_iso_dttm_ser),
        )

    @api
    @handle_api_exception
    @has_access_api
    @expose("/slice_query/<slice_id>/")
    def slice_query(self, slice_id):
        """
        This method exposes an API endpoint to
        get the database query string for this slice
        """
        viz_obj = get_viz(slice_id)
        security_manager.assert_datasource_permission(viz_obj.datasource)
        return self.get_query_string_response(viz_obj)

    @api
    @has_access_api
    @expose("/schemas_access_for_csv_upload")
    def schemas_access_for_csv_upload(self):
        """
        This method exposes an API endpoint to
        get the schema access control settings for csv upload in this database
        """
        if not request.args.get("db_id"):
            return json_error_response("No database is allowed for your csv upload")

        db_id = int(request.args.get("db_id"))
        database = db.session.query(models.Database).filter_by(id=db_id).one()
        try:
            schemas_allowed = database.get_schema_access_for_csv_upload()
            if (
                security_manager.database_access(database)
                or security_manager.all_datasource_access()
            ):
                return self.json_response(schemas_allowed)
            # the list schemas_allowed should not be empty here
            # and the list schemas_allowed_processed returned from security_manager
            # should not be empty either,
            # otherwise the database should have been filtered out
            # in CsvToDatabaseForm
            schemas_allowed_processed = security_manager.schemas_accessible_by_user(
                database, schemas_allowed, False
            )
            return self.json_response(schemas_allowed_processed)
        except Exception:
            return json_error_response(
                "Failed to fetch schemas allowed for csv upload in this database! "
                "Please contact Superset Admin!",
                stacktrace=utils.get_stacktrace(),
            )


appbuilder.add_view_no_menu(Superset)


class CssTemplateModelView(SupersetModelView, DeleteMixin):
    datamodel = SQLAInterface(models.CssTemplate)

    list_title = _("CSS Templates")
    show_title = _("Show CSS Template")
    add_title = _("Add CSS Template")
    edit_title = _("Edit CSS Template")

    list_columns = ["template_name"]
    edit_columns = ["template_name", "css"]
    add_columns = edit_columns
    label_columns = {"template_name": _("Template Name")}


class CssTemplateAsyncModelView(CssTemplateModelView):
    list_columns = ["template_name", "css"]


appbuilder.add_separator("Sources")
appbuilder.add_view(
    CssTemplateModelView,
    "CSS Templates",
    label=__("CSS Templates"),
    icon="fa-css3",
    category="Manage",
    category_label=__("Manage"),
    category_icon="",
)

appbuilder.add_view_no_menu(CssTemplateAsyncModelView)

appbuilder.add_link(
    "SQL Editor",
    label=_("SQL Editor"),
    href="/superset/sqllab",
    category_icon="fa-flask",
    icon="fa-flask",
    category="SQL Lab",
    category_label=__("SQL Lab"),
)

appbuilder.add_link(
    "Query Search",
    label=_("Query Search"),
    href="/superset/sqllab#search",
    icon="fa-search",
    category_icon="fa-flask",
    category="SQL Lab",
    category_label=__("SQL Lab"),
)

appbuilder.add_link(
    "Upload a CSV",
    label=__("Upload a CSV"),
    href="/csvtodatabaseview/form",
    icon="fa-upload",
    category="Sources",
    category_label=__("Sources"),
    category_icon="fa-wrench",
)
appbuilder.add_separator("Sources")


@app.after_request
def apply_http_headers(response):
    """Applies the configuration's http headers to all responses"""
    for k, v in config.get("HTTP_HEADERS").items():
        response.headers[k] = v
    return response


# ---------------------------------------------------------------------
# Redirecting URL from previous names
class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters["regex"] = RegexConverter


@app.route('/<regex("panoramix\/.*"):url>')
def panoramix(url):
    return redirect(request.full_path.replace("panoramix", "superset"))


@app.route('/<regex("caravel\/.*"):url>')
def caravel(url):
    return redirect(request.full_path.replace("caravel", "superset"))

# ---------------------------------------------------------------------
