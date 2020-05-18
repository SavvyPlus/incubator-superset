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
from sqlalchemy import Column, ForeignKey, Integer, String, Table, Date, DateTime
from sqlalchemy.orm import make_transient, relationship

from superset import ConnectorRegistry, db, is_feature_enabled, security_manager
from superset.legacy import update_time_range
from superset.models.helpers import AuditMixinNullable, ImportMixin
from superset.models.tags import ChartUpdater
from superset.utils import core as utils
from superset.viz import BaseViz, viz_types

class Client(Model):
    __tablename__ = "client"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500))

    def __repr__(self):
        return self.name


class Project(Model):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500))
    client_id = Column(Integer, ForeignKey("client.id"))
    client = relationship("Client", foreign_keys=[client_id], backref="projects")

    def __repr__(self):
        return self.name


class Assumption(
    Model
):
    __tablename__ = "assumption"
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    description = Column(String(200))
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
    description = Column(String(200))
    assumption_id = Column(Integer, ForeignKey("assumption.id"))
    assumption = relationship("Assumption", foreign_keys=[assumption_id])
    project_id = Column(Integer, ForeignKey("project.id"))
    project = relationship("Project", foreign_keys=[project_id], backref="simulations")
    generation_model = Column(String(20))
    run_no = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    report_type = Column(String(200))
    status = Column(String(10))
    status_detail = Column(String(500))

    def __repr__(self):
        return self.name


class SimulationLog(Model):
    __tablename__ = "simulation_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("ab_user.id"))
    user = relationship(
        security_manager.user_model, foreign_keys=[user_id]
    )
    action = Column(String(512))
    action_object = Column(String(512))
    action_object_type = Column(String(20))
    dttm = Column(DateTime)
    result = Column(String(20))
    detail = Column(String(512))
