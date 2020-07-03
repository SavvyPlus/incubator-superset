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
from sqlalchemy import Column, ForeignKey, Integer, String, Table, Date, DateTime, Text, func, Float
from sqlalchemy.orm import make_transient, relationship

from superset import ConnectorRegistry, db, is_feature_enabled, security_manager
from superset.legacy import update_time_range
from superset.models.helpers import AuditMixinNullable, ImportMixin
from superset.models.tags import ChartUpdater
from superset.utils import core as utils
from superset.viz import BaseViz, viz_types
from superset.views.simulation.simulation_config import *


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
    s3_path = Column(String(200))

    def __repr__(self):
        return self.name

def find_assumption_by_name(session, name):
    return session.query(Assumption).filter_by(name=func.binary(name)).one_or_none()

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
    run_id = Column(String(20))
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
    status = Column(String(128))
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
    result = Column(String(128))
    detail = Column(Text)



"""Rooftop Solar History"""
class RooftopSolarHistoryDefinition(Model):
    __tablename__ = "Rooftop_Solar_History_Definition"
    Rooftop_Solar_History_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Rooftop_Solar_History_Version

    @staticmethod
    def get_sheet_name():
        return sheet_pv_history

class RooftopSolarHistory(Model):
    __tablename__ = "Rooftop_Solar_History"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Date = Column(Date)
    Capacity_MW = Column(Float)
    Aggregate_MW = Column(Float)
    Rooftop_Solar_History_Version = Column(Integer,
                                           ForeignKey('Rooftop_Solar_History_Definition.Rooftop_Solar_History_Version'),
                                           nullable=False)
    Rooftop_Solar_History_Definition = relationship('RooftopSolarHistoryDefinition',
                                                    foreign_keys=[Rooftop_Solar_History_Version],
                                                    backref="data")

    def set_version(self, version):
        self.Rooftop_Solar_History_Version = version

    @staticmethod
    def get_version_col_name():
        return 'Rooftop_Solar_History_Version'

"""Rooftop Solar Forecast"""
class RooftopSolarForecastDefinition(Model):
    __tablename__ = "Rooftop_Solar_Forecast_Definition"
    Rooftop_Solar_Forecast_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))
    Assumption_Scenario = Column(String(50))
    Assumption_Scenario_Version = Column(Integer)

    def get_version(self):
        return self.Rooftop_Solar_Forecast_Version

    @staticmethod
    def get_sheet_name():
        return sheet_pv_forecast

class RooftopSolarForecast(Model):
    __tablename__ = "Rooftop_Solar_Forecast"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Year = Column(Integer)
    Capacity_MW = Column(Float)
    Aggregate_MW = Column(Float)
    Rooftop_Solar_Forecast_Version = Column(Integer,
                                           ForeignKey('Rooftop_Solar_Forecast_Definition.Rooftop_Solar_Forecast_Version'),
                                           nullable=False)
    Rooftop_Solar_Forecast_Definition = relationship('RooftopSolarForecastDefinition',
                                                    foreign_keys=[Rooftop_Solar_Forecast_Version],
                                                    backref="data")

    def set_version(self, version):
        self.Rooftop_Solar_Forecast_Version = version

    @staticmethod
    def get_version_col_name():
        return 'Rooftop_Solar_Forecast_Version'

"""Renewable Proportion"""
class RenewableProportionDefinition(Model):
    __tablename__ = "Renewable_Proportion_Definition"
    Renewable_Proportion_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Renewable_Proportion_Version

    @staticmethod
    def get_sheet_name():
        return sheet_renewable_proportion

class RenewableProportion(Model):
    __tablename__ = "Renewable_Proportion"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Date = Column(Date)
    Maximum_HalfHour_Intermittent_Proportion = Column(Float)
    Renewable_Proportion_Version = Column(Integer,
                                           ForeignKey('Renewable_Proportion_Definition.Renewable_Proportion_Version'),
                                           nullable=False)
    Renewable_Proportion_Definition = relationship('RenewableProportionDefinition',
                                                    foreign_keys=[Renewable_Proportion_Version],
                                                    backref="data")

    def set_version(self, version):
        self.Renewable_Proportion_Version = version

    @staticmethod
    def get_version_col_name():
        return 'Renewable_Proportion_Version'


"""Demand Growth"""
class DemandGrowthDefinition(Model):
    __tablename__ = "Demand_Growth_Definition"
    Demand_Growth_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))
    Assumption_Scenario = Column(String(50))
    Assumption_Scenario_Version = Column(Integer)

    def get_version(self):
        return self.Demand_Growth_Version

    @staticmethod
    def get_sheet_name():
        return sheet_demand_growth

class DemandGrowth(Model):
    __tablename__ = "Demand_Growth"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Year = Column(Integer)
    Probability = Column(Float)
    Growth = Column(Float)
    Demand_Growth_Version = Column(Integer,
                                           ForeignKey('Demand_Growth_Definition.Demand_Growth_Version'),
                                           nullable=False)
    Demand_Growth_Definition = relationship('DemandGrowthDefinition',
                                                    foreign_keys=[Demand_Growth_Version],
                                                    backref="data")

    def set_version(self, version):
        self.Demand_Growth_Version = version

    @staticmethod
    def get_version_col_name():
        return 'Demand_Growth_Version'

"""Behind The Meter Battery"""
class BehindTheMeterBatteryDefinition(Model):
    __tablename__ = "Behind_The_Meter_Battery_Definition"
    Behind_The_Meter_Battery_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))
    Assumption_Scenario = Column(String(50))
    Assumption_Scenario_Version = Column(Integer)

    def get_version(self):
        return self.Behind_The_Meter_Battery_Version

    @staticmethod
    def get_sheet_name():
        return sheet_behind_the_meter_battery

class BehindTheMeterBattery(Model):
    __tablename__ = "Behind_The_Meter_Battery"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Year = Column(Integer)
    Aggregate_MW = Column(Float)
    Behind_The_Meter_Battery_Version = Column(Integer,
                                           ForeignKey('Behind_The_Meter_Battery_Definition.Behind_The_Meter_Battery_Version'),
                                           nullable=False)
    Behind_The_Meter_Battery_Definition = relationship('BehindTheMeterBatteryDefinition',
                                                    foreign_keys=[Behind_The_Meter_Battery_Version],
                                                    backref="data")

    def set_version(self, version):
        self.Behind_The_Meter_Battery_Version = version

    @staticmethod
    def get_version_col_name():
        return 'Behind_The_Meter_Battery_Version'

"""Project Proxy"""
class ProjectProxyDefinition(Model):
    __tablename__ = "Project_Proxy_Definition"
    Project_Proxy_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Project_Proxy_Version

    @staticmethod
    def get_sheet_name():
        return sheet_project_proxy

class ProjectProxy(Model):
    __tablename__ = "Project_Proxy"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Project = Column(String(50))
    Nameplate_Capacity_MW = Column(Float)
    Technology_Type = Column(String(10))
    Latitude = Column(Float)
    Longitude = Column(Float)
    Tracking_Type = Column(String(50))
    Project_Proxy_Version = Column(Integer,
                                   ForeignKey('Project_Proxy_Definition.Project_Proxy_Version'),
                                   nullable=False)
    Project_Proxy_Definition = relationship('ProjectProxyDefinition',
                                            foreign_keys=[Project_Proxy_Version],
                                            backref="data")

    def set_version(self, version):
        self.Project_Proxy_Version = version

    @staticmethod
    def get_version_col_name():
        return 'Project_Proxy_Version'

"""MPC CPT"""
class MPCCPTDefinition(Model):
    __tablename__ = "MPC_CPT_Definition"
    MPC_CPT_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.MPC_CPT_Version

    @staticmethod
    def get_sheet_name():
        return sheet_mpc

class MPCCPT(Model):
    __tablename__ = "MPC_CPT"
    id = Column(Integer, primary_key=True, autoincrement=True)
    FY = Column(String(10))
    CPT = Column(Float)
    MPC = Column(Float)
    MPC_CPT_Version = Column(Integer,
                            ForeignKey('MPC_CPT_Definition.MPC_CPT_Version'),
                            nullable=False)
    MPC_CPT_Definition = relationship('MPCCPTDefinition',
                                    foreign_keys=[MPC_CPT_Version],
                                    backref="data")

    def set_version(self, version):
        self.MPC_CPT_Version = version

    @staticmethod
    def get_version_col_name():
        return 'MPC_CPT_Version'

"""Gas Price Escalation"""
class GasPriceEscalationDefinition(Model):
    __tablename__ = "Gas_Price_Escalation_Definition"
    Gas_Price_Escalation_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Gas_Price_Escalation_Version

    @staticmethod
    def get_sheet_name():
        return sheet_escalation

class GasPriceEscalation(Model):
    __tablename__ = "Gas_Price_Escalation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Year = Column(Integer)
    Case1 = Column(Float)
    Case2 = Column(Float)
    Case3 = Column(Float)
    Case4 = Column(Float)
    Case5 = Column(Float)
    Case6 = Column(Float)
    Case7 = Column(Float)
    Case8 = Column(Float)
    Case9 = Column(Float)
    Gas_Price_Escalation_Version = Column(Integer,
                                        ForeignKey('Gas_Price_Escalation_Definition.Gas_Price_Escalation_Version'),
                                        nullable=False)
    Gas_Price_Escalation_Definition = relationship('GasPriceEscalationDefinition',
                                                    foreign_keys=[Gas_Price_Escalation_Version],
                                                    backref="data")

    def set_version(self, version):
        self.Gas_Price_Escalation_Version = version

    @staticmethod
    def get_version_col_name():
        return 'Gas_Price_Escalation_Version'

"""Strategy Behaviour"""
class StrategicBehaviourDefinition(Model):
    __tablename__ = "Strategic_Behaviour_Definition"
    Strategic_Behaviour_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Strategic_Behaviour_Version

    @staticmethod
    def get_sheet_name():
        return sheet_strategic_behaviour

class StrategicBehaviour(Model):
    __tablename__ = "Strategic_Behaviour"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Bin_Not_Exceeding = Column(Integer)
    Value = Column(Float)
    MW = Column(Float)
    Strategic_Behaviour_Version = Column(Integer,
                            ForeignKey('Strategic_Behaviour_Definition.Strategic_Behaviour_Version'),
                            nullable=False)
    Strategic_Behaviour_Definition = relationship('StrategicBehaviourDefinition',
                                    foreign_keys=[Strategic_Behaviour_Version],
                                    backref="data")

    def set_version(self, version):
        self.Strategic_Behaviour_Version = version

    @staticmethod
    def get_version_col_name():
        return 'Strategic_Behaviour_Version'

"""Retirement"""
class RetirementDefinition(Model):
    __tablename__ = "Retirement_Definition"
    Retirement_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Retirement_Version

    @staticmethod
    def get_sheet_name():
        return sheet_retirement

class Retirement(Model):
    __tablename__ = "Retirement"
    id = Column(Integer, primary_key=True, autoincrement=True)
    DUID = Column(String(50))
    State = Column(String(10))
    Registered_Capacity = Column(Float)
    Impact_To_State = Column(String(10))
    Adjustment_Factor = Column(Float)
    Closure_Date = Column(Date)
    Back_To_Service_Date = Column(Date)
    Retirement_Version = Column(Integer,
                            ForeignKey('Retirement_Definition.Retirement_Version'),
                            nullable=False)
    Retirement_Definition = relationship('RetirementDefinition',
                                    foreign_keys=[Retirement_Version],
                                    backref="data")

    def set_version(self, version):
        self.Retirement_Version = version

    @staticmethod
    def get_version_col_name():
        return 'Retirement_Version'

"""Project List"""
class ProjectListDefinition(Model):
    __tablename__ = "Project_List_Definition"
    Project_List_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Project_List_Version

    @staticmethod
    def get_sheet_name():
        return sheet_project_list

class ProjectList(Model):
    __tablename__ = "Project_List"
    id = Column(Integer, primary_key=True, autoincrement=True)
    DUID = Column(String(50))
    Name = Column(String(50))
    State = Column(String(10))
    Fuel_Type = Column(String(10))
    Start_Date = Column(Date)
    End_Date = Column(Date)
    Status = Column(String(50))
    Offer_Rate = Column(Float)
    Maximum_Quantity = Column(Float)
    Installed_Quantity = Column(Float)
    Probability_Of_Success = Column(Float)
    Resolution = Column(String(20))
    Proxy = Column(String(50))
    Project_List_Version = Column(Integer,
                            ForeignKey('Project_List_Definition.Project_List_Version'),
                            nullable=False)
    Project_List_Definition = relationship('ProjectListDefinition',
                                    foreign_keys=[Project_List_Version],
                                    backref="data")

    def set_version(self, version):
        self.Project_List_Version = version

    @staticmethod
    def get_version_col_name():
        return 'Project_List_Version'


model_list = {
    (RooftopSolarHistoryDefinition, RooftopSolarHistory),
    (RooftopSolarForecastDefinition, RooftopSolarForecast),
    (RenewableProportionDefinition, RenewableProportion),
    (DemandGrowthDefinition, DemandGrowth),
    (BehindTheMeterBatteryDefinition, BehindTheMeterBattery),
    (ProjectProxyDefinition, ProjectProxy),
    (MPCCPTDefinition, MPCCPT),
    (GasPriceEscalationDefinition, GasPriceEscalation),
    (StrategicBehaviourDefinition, StrategicBehaviour),
    (RetirementDefinition, Retirement),
    (ProjectListDefinition, ProjectList)
}


class AssumptionDefinition(Model):
    __tablename__ = "Assumption_Definition"
    id = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(20))
    Note = Column(String(512))
    Rooftop_Solar_History_Version = Column(Integer,
                                           ForeignKey('Rooftop_Solar_History_Definition.Rooftop_Solar_History_Version'))
    Rooftop_Solar_History_Definition = relationship('RooftopSolarHistoryDefinition',
                                                    foreign_keys=[Rooftop_Solar_History_Version])

    Rooftop_Solar_Forecast_Version = Column(Integer,
                                           ForeignKey('Rooftop_Solar_Forecast_Definition.Rooftop_Solar_Forecast_Version'))
    Rooftop_Solar_Forecast_Definition = relationship('RooftopSolarForecastDefinition',
                                                    foreign_keys=[Rooftop_Solar_Forecast_Version])

    Renewable_Proportion_Version = Column(Integer,
                                           ForeignKey('Renewable_Proportion_Definition.Renewable_Proportion_Version'))
    Renewable_Proportion_Definition = relationship('RenewableProportionDefinition',
                                                    foreign_keys=[Renewable_Proportion_Version])

    Demand_Growth_Version = Column(Integer,
                                           ForeignKey('Demand_Growth_Definition.Demand_Growth_Version'))
    Demand_Growth_Definition = relationship('DemandGrowthDefinition',
                                                    foreign_keys=[Demand_Growth_Version])

    Behind_The_Meter_Battery_Version = Column(Integer,
                                           ForeignKey('Behind_The_Meter_Battery_Definition.Behind_The_Meter_Battery_Version'))
    Behind_The_Meter_Battery_Definition = relationship('BehindTheMeterBatteryDefinition',
                                                    foreign_keys=[Behind_The_Meter_Battery_Version])

    Project_Proxy_Version = Column(Integer,
                                   ForeignKey('Project_Proxy_Definition.Project_Proxy_Version'))
    Project_Proxy_Definition = relationship('ProjectProxyDefinition',
                                            foreign_keys=[Project_Proxy_Version])

    MPC_CPT_Version = Column(Integer,
                            ForeignKey('MPC_CPT_Definition.MPC_CPT_Version'))
    MPC_CPT_Definition = relationship('MPCCPTDefinition',
                                    foreign_keys=[MPC_CPT_Version])

    Gas_Price_Escalation_Version = Column(Integer,
                                        ForeignKey('Gas_Price_Escalation_Definition.Gas_Price_Escalation_Version'))
    Gas_Price_Escalation_Definition = relationship('GasPriceEscalationDefinition',
                                                    foreign_keys=[Gas_Price_Escalation_Version])

    Strategic_Behaviour_Version = Column(Integer,
                            ForeignKey('Strategic_Behaviour_Definition.Strategic_Behaviour_Version'))
    Strategic_Behaviour_Definition = relationship('StrategicBehaviourDefinition',
                                    foreign_keys=[Strategic_Behaviour_Version])

    Retirement_Version = Column(Integer,
                            ForeignKey('Retirement_Definition.Retirement_Version'))
    Retirement_Definition = relationship('RetirementDefinition',
                                    foreign_keys=[Retirement_Version])

    Project_List_Version = Column(Integer,
                            ForeignKey('Project_List_Definition.Project_List_Version'))
    Project_List_Definition = relationship('ProjectListDefinition',
                                    foreign_keys=[Project_List_Version])