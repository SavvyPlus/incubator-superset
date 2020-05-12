import json
import traceback
import logging
import os
import tempfile
from flask import flash, redirect, g, request, abort
from flask_appbuilder.widgets import ListWidget
from flask_appbuilder.security.sqla import models as ab_models
from flask_appbuilder import expose, has_access, SimpleFormView
from flask_appbuilder.urltools import get_filter_args, get_order_args, get_page_args, get_page_size_args
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_babel import lazy_gettext as _

from superset import app, db, event_logger, simulation_logger, celery_app
from superset.connectors.connector_registry import ConnectorRegistry
from superset.constants import RouteMethod
from superset.models.simulation import Assumption, Simulation, SimulationLog
from superset.utils import core as utils
from superset.views.base import check_ownership, DeleteMixin, SupersetModelView
from superset.models.slice import Slice

from ..base import (
    api,
    BaseSupersetView,
    check_ownership,
    common_bootstrap_payload,
    create_table_permissions,
    CsvResponse,
    data_payload_response,
    DeleteMixin,
    generate_download_headers,
    get_error_msg,
    get_user_roles,
    handle_api_exception,
    json_error_response,
    json_success,
    SupersetModelView,
    validate_sqlatable,
)
from ..utils import (
    apply_display_max_row_limit,
    bootstrap_user_data,
    get_datasource_info,
    get_form_data,
    get_viz,
)


class NemModelView(
    SupersetModelView, DeleteMixin
):  # pylint: disable=too-many-ancestors
    route_base = "/nem"
    default_view = 'generation'
    datamodel = SQLAInterface(Slice)

    @expose("/generation/")
    # @has_access
    def generation(self):
        username = g.user.username

        user = (
            db.session.query(ab_models.User).filter_by(username=username).one_or_none()
        )
        if not user:
            abort(404, description=f"User: {username} does not exist.")

        payload = {
            "user": bootstrap_user_data(user, include_perms=True),
            "common": common_bootstrap_payload(),
        }

        return self.render_template(
            "superset/basic.html",
            title=_("NEM Energy"),
            entry="generation",
            bootstrap_data=json.dumps(
                payload, default=utils.pessimistic_json_iso_dttm_ser
            ),
        )
