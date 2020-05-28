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


class Region(Model):
    __tablename__ = "region"
    id = Column(Integer, primary_key=True)
    name = Column(String(8), nullable=False, unique=True)
    sql_repr = Column(String(8), nullable=False)

    def __repr__(self):
        return self.name

class Client(Model):
    __tablename__ = "client"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(String(500))

    def __repr__(self):
        return self.name

class JobType(Model):
    __tablename__ = "job_type"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, unique=True)

    def __repr__(self):
        return self.name

project_jobtype = Table(
    "project_jobtype",
    Model.metadata,
    Column("id", Integer, primary_key=True),
    Column("project_id", Integer, ForeignKey("project.id")),
    Column("jobtype_id", Integer, ForeignKey("job_type.id")),
)

project_region = Table(
    "project_region",
    Model.metadata,
    Column("id", Integer, primary_key=True),
    Column("project_id", Integer, ForeignKey("project.id")),
    Column("region_id", Integer, ForeignKey("region.id")),
)


class Project(Model):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=False)
    description = Column(String(500))
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False)
    client = relationship("Client", foreign_keys=[client_id], backref="projects")
    region = relationship("Region", secondary=project_region)
    job_types = relationship("JobType", secondary=project_jobtype)
    due_date = Column(Date, default='9999-12-31')

    def __repr__(self):
        return self.name


class Assumption(
    Model
):
    __tablename__ = "assumption"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(200))
    status = Column(String(10))
    status_detail = Column(String(500))
    download_link = Column(String(200))

    def __repr__(self):
        return self.name

simulation_jobtype = Table(
    "simulation_jobtype",
    Model.metadata,
    Column("id", Integer, primary_key=True),
    Column("simulation_id", Integer, ForeignKey("simulation.id")),
    Column("jobtype_id", Integer, ForeignKey("job_type.id")),
)


class Simulation(
    Model
):
    __tablename__ = "simulation"
    id = Column(Integer, primary_key=True)
    run_id = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(String(200))
    assumption_id = Column(Integer, ForeignKey("assumption.id"), nullable=False)
    assumption = relationship("Assumption", foreign_keys=[assumption_id])
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    project = relationship("Project", foreign_keys=[project_id], backref="simulations")
    run_no = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    # report_type = Column(String(200), nullable=False)
    report_type = relationship("JobType", secondary=simulation_jobtype)
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
