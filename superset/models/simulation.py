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
import logging
from typing import Any, Dict, Optional, Type, TYPE_CHECKING
from urllib import parse

import sqlalchemy as sqla
from flask_appbuilder import Model
from flask_appbuilder.models.decorators import renders
from markupsafe import escape, Markup
from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import make_transient, relationship

from superset import ConnectorRegistry, db, is_feature_enabled, security_manager
from superset.legacy import update_time_range
from superset.models.helpers import AuditMixinNullable, ImportMixin
from superset.models.tags import ChartUpdater
from superset.utils import core as utils
from superset.viz import BaseViz, viz_types

simulation_assumption = Table(
    "simulation_assumption",
    Model.metadata,
    Column("id", Integer, primary_key=True),
    Column("simulation_id", Integer, ForeignKey("simulation.id")),
    Column("assumption_id", Integer, ForeignKey("assumption.id")),
)

class Assumption(
    Model
):
    __tablename__ = "assumption"
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    s3_path = Column(String(500))
    status = Column(String(10))
    status_detail = Column(String(500))
    download_link = Column(String(200))

    def __repr__(self):
        return self.name

class Simulation(
    Model
):
    __tablename__ = "simulation"
    id = Column(Integer, primary_key=True)
    run_id = Column(String(20))
    name = Column(String(200))
    assumption = relationship("Assumption", secondary=simulation_assumption, backref="simulation")
    status = Column(String(10))
    status_detail = Column(String(500))