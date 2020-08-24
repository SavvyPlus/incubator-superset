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
from sqlalchemy import Column, ForeignKey, Integer, String, Table, Date, DateTime, Text, func, DECIMAL, Float
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
    run_dttm = Column(DateTime)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    # report_type = Column(String(200), nullable=False)
    report_type = relationship("JobType", secondary=simulation_jobtype)
    status = Column(String(128))
    status_detail = Column(String(500))

    def __repr__(self):
        return self.name

class ChartLink(Model):
    __tablename__ = 'chart_simulation'
    id = Column(Integer, primary_key=True)
    chart_name = Column(String(128))
    simulation_id = Column(Integer, ForeignKey("simulation.id"), nullable=False)
    simulation = relationship("Simulation", foreign_keys=[simulation_id], backref="chart_links")
    chart_link = Column(String(1024))

    def __repr__(self):
        return self.chart_name

    def __init__(self, chart_name, simulation, chart_link):
        self.chart_name = chart_name
        self.simulation = simulation
        self.simulation_id = simulation.id
        self.chart_link = chart_link

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

"""Data table interface"""
class DataTableMixin:

    __tablename__ = None
    included_keys = None
    column_type_dict = None

    def __init__(self, **kwargs):
        for key in kwargs.keys():
            self.__setattr__(key, kwargs[key])

    def get_def_col_name(self):
        return self.__tablename__ + '_Definition'

    def get_definition(self):
        return getattr(self, self.get_def_col_name())

    def get_dict(self):
        return dict((key, value) for (key, value) in self.__dict__.items() if key in self.column_type_dict.keys())

    def get_header_and_type(self):
        return [{'name': key, 'type': self.column_type_dict[key]} for key in self.column_type_dict.keys() ]

    @staticmethod
    def get_version_col_name():
        return 'Version'

class DefTableMixin:
    Note = None
    Assumption_Scenario = None
    Assumption_Scenario_Version = None

    def set_scenario(self, scenario, version=1):
        self.Assumption_Scenario = scenario
        self.Assumption_Scenario_Version = version

    def get_scenario(self):
        return self.Assumption_Scenario

    def set_note(self, note):
        self.Note = note

    def get_note(self):
        return self.Note

"""Rooftop Solar History"""
class RooftopSolarHistoryDefinition(Model, DefTableMixin):
    __tablename__ = "Rooftop_Solar_History_Definition"
    Rooftop_Solar_History_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Rooftop_Solar_History_Version

    @staticmethod
    def get_sheet_name():
        return sheet_pv_history

class RooftopSolarHistory(Model, DataTableMixin):
    __tablename__ = "Rooftop_Solar_History"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Date = Column(Date)
    Capacity_MW = Column(DECIMAL(32,16))
    Aggregate_MW = Column(DECIMAL(32,16))
    Version = Column(Integer,
                                           ForeignKey('Rooftop_Solar_History_Definition.Rooftop_Solar_History_Version'),
                                           nullable=False)
    Rooftop_Solar_History_Definition = relationship('RooftopSolarHistoryDefinition',
                                                    foreign_keys=[Version],
                                                    backref="data")
    included_keys = ['State', 'Date', 'Capacity_MW', 'Aggregate_MW']
    column_type_dict = {'State':'string','Date':'date','Capacity_MW': 'numeric', 'Aggregate_MW': 'numeric'}


"""Rooftop Solar Forecast"""
class RooftopSolarForecastDefinition(Model, DefTableMixin):
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

class RooftopSolarForecast(Model, DataTableMixin):
    __tablename__ = "Rooftop_Solar_Forecast"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Year = Column(Integer)
    Aggregate_MW = Column(DECIMAL(32,16))
    Version = Column(Integer,
                                           ForeignKey('Rooftop_Solar_Forecast_Definition.Rooftop_Solar_Forecast_Version'),
                                           nullable=False)
    Rooftop_Solar_Forecast_Definition = relationship('RooftopSolarForecastDefinition',
                                                    foreign_keys=[Version],
                                                    backref="data")
    included_keys = ['State', 'Year', 'Aggregate_MW']
    column_type_dict = {'State': 'string', 'Year':'numeric', 'Aggregate_MW': 'numeric'}


"""Renewable Proportion"""
class RenewableProportionDefinition(Model, DefTableMixin):
    __tablename__ = "Renewable_Proportion_Definition"
    Renewable_Proportion_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Renewable_Proportion_Version

    @staticmethod
    def get_sheet_name():
        return sheet_renewable_proportion

class RenewableProportion(Model, DataTableMixin):
    __tablename__ = "Renewable_Proportion"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Date = Column(Date)
    Maximum_HalfHour_Intermittent_Proportion = Column(DECIMAL(5,4))
    Version = Column(Integer,
                                           ForeignKey('Renewable_Proportion_Definition.Renewable_Proportion_Version'),
                                           nullable=False)
    Renewable_Proportion_Definition = relationship('RenewableProportionDefinition',
                                                    foreign_keys=[Version],
                                                    backref="data")
    included_keys = ['State', 'Date', 'Maximum_HalfHour_Intermittent_Proportion']
    column_type_dict = {'State':'string', 'Date':'date', 'Maximum_HalfHour_Intermittent_Proportion': 'numeric'}


"""Demand Growth"""
class DemandGrowthDefinition(Model, DefTableMixin):
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

class DemandGrowth(Model, DataTableMixin):
    __tablename__ = "Demand_Growth"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Year = Column(Integer)
    Probability = Column(DECIMAL(5,4))
    Growth = Column(DECIMAL(7,6))
    Version = Column(Integer,
                   ForeignKey('Demand_Growth_Definition.Demand_Growth_Version'),
                   nullable=False)
    Demand_Growth_Definition = relationship('DemandGrowthDefinition',
                                                    foreign_keys=[Version],
                                                    backref="data")
    included_keys = ['State', 'Year', 'Probability', 'Growth']
    column_type_dict = {'State':'string' ,'Year':'numeric' ,'Probability':'numeric', 'Growth':'numeric'}


"""Behind The Meter Battery"""
class BehindTheMeterBatteryDefinition(Model, DefTableMixin):
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

class BehindTheMeterBattery(Model, DataTableMixin):
    __tablename__ = "Behind_The_Meter_Battery"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Year = Column(Integer)
    Aggregate_MW = Column(DECIMAL(32,16))
    Version = Column(Integer,
                                           ForeignKey('Behind_The_Meter_Battery_Definition.Behind_The_Meter_Battery_Version'),
                                           nullable=False)
    Behind_The_Meter_Battery_Definition = relationship('BehindTheMeterBatteryDefinition',
                                                    foreign_keys=[Version],
                                                    backref="data")
    included_keys = ['State', 'Year', 'Aggregate_MW']
    column_type_dict = {'State':'string','Year':'numeric','Aggregate_MW':'numeric'}


"""Project Proxy"""
class ProjectProxyDefinition(Model, DefTableMixin):
    __tablename__ = "Project_Proxy_Definition"
    Project_Proxy_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Project_Proxy_Version

    @staticmethod
    def get_sheet_name():
        return sheet_project_proxy

class ProjectProxy(Model, DataTableMixin):
    __tablename__ = "Project_Proxy"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Project = Column(String(50))
    Nameplate_Capacity_MW = Column(DECIMAL(32,16))
    Technology_Type = Column(String(10))
    Latitude = Column(DECIMAL(32,16))
    Longitude = Column(DECIMAL(32,16))
    Tracking_Type = Column(String(50))
    Version = Column(Integer,
                                   ForeignKey('Project_Proxy_Definition.Project_Proxy_Version'),
                                   nullable=False)
    Project_Proxy_Definition = relationship('ProjectProxyDefinition',
                                            foreign_keys=[Version],
                                            backref="data")
    included_keys = ['State', 'Project', 'Nameplate_Capacity_MW', 'Technology_Type', 'Latitude', 'Longitude', 'Tracking_Type']
    column_type_dict = {'State':'string', 'Project':'string', 'Nameplate_Capacity_MW': 'numeric',
                        'Technology_Type': 'string', 'Latitude':'numeric', 'Longitude':'numeric', 'TTracking_Typerac':'string'}


"""MPC CPT"""
class MPCCPTDefinition(Model, DefTableMixin):
    __tablename__ = "MPC_CPT_Definition"
    MPC_CPT_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.MPC_CPT_Version

    @staticmethod
    def get_sheet_name():
        return sheet_mpc

class MPCCPT(Model, DataTableMixin):
    __tablename__ = "MPC_CPT"
    id = Column(Integer, primary_key=True, autoincrement=True)
    FY = Column(String(10))
    CPT = Column(DECIMAL(32,16))
    MPC = Column(DECIMAL(32,16))
    Version = Column(Integer,
                            ForeignKey('MPC_CPT_Definition.MPC_CPT_Version'),
                            nullable=False)
    MPC_CPT_Definition = relationship('MPCCPTDefinition',
                                    foreign_keys=[Version],
                                    backref="data")
    included_keys = ['FY', 'CPT', 'MPC']
    column_type_dict = {'FY': 'string', 'CPT': 'numeric', 'MPC':'numeric'}


"""Gas Price Escalation"""
class GasPriceEscalationDefinition(Model, DefTableMixin):
    __tablename__ = "Gas_Price_Escalation_Definition"
    Gas_Price_Escalation_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Gas_Price_Escalation_Version

    @staticmethod
    def get_sheet_name():
        return sheet_escalation

class GasPriceEscalation(Model, DataTableMixin):
    __tablename__ = "Gas_Price_Escalation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Year = Column(Integer)
    Case1 = Column(DECIMAL(7,6))
    Case2 = Column(DECIMAL(7,6))
    Case3 = Column(DECIMAL(7,6))
    Case4 = Column(DECIMAL(7,6))
    Case5 = Column(DECIMAL(7,6))
    Case6 = Column(DECIMAL(7,6))
    Case7 = Column(DECIMAL(7,6))
    Case8 = Column(DECIMAL(7,6))
    Case9 = Column(DECIMAL(7,6))
    Version = Column(Integer,
                                        ForeignKey('Gas_Price_Escalation_Definition.Gas_Price_Escalation_Version'),
                                        nullable=False)
    Gas_Price_Escalation_Definition = relationship('GasPriceEscalationDefinition',
                                                    foreign_keys=[Version],
                                                    backref="data")
    included_keys = ['State', 'Year', 'Case1', 'Case2', 'Case3', 'Case4', 'Case5', 'Case6', 'Case7', 'Case8', 'Case9']
    column_type_dict = {'State': 'string', 'Year':'numeric', 'Case1':'numeric', 'Case2':'numeric', 'Case3':'numeric',
                        'Case4':'numeric', 'Case5':'numeric', 'Case6':'numeric', 'Case7':'numeric', 'Case8':'numeric',
                        'Case9':'numeric'}


"""Strategy Behaviour"""
class StrategicBehaviourDefinition(Model, DefTableMixin):
    __tablename__ = "Strategic_Behaviour_Definition"
    Strategic_Behaviour_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Strategic_Behaviour_Version

    @staticmethod
    def get_sheet_name():
        return sheet_strategic_behaviour

class StrategicBehaviour(Model, DataTableMixin):
    __tablename__ = "Strategic_Behaviour"
    id = Column(Integer, primary_key=True, autoincrement=True)
    State = Column(String(10))
    Bin_Not_Exceeding = Column(Integer)
    Value = Column(DECIMAL(7,6))
    MW = Column(DECIMAL(32,16))
    Version = Column(Integer,
                            ForeignKey('Strategic_Behaviour_Definition.Strategic_Behaviour_Version'),
                            nullable=False)
    Strategic_Behaviour_Definition = relationship('StrategicBehaviourDefinition',
                                    foreign_keys=[Version],
                                    backref="data")
    included_keys = ['State', 'Bin_Not_Exceeding', 'Value', 'MW']
    column_type_dict = {'State':'string', 'Bin_Not_Exceeding': 'numeric', 'value':'numeric', 'MW':'numeric'}

"""Retirement"""
class RetirementDefinition(Model, DefTableMixin):
    __tablename__ = "Retirement_Definition"
    Retirement_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Retirement_Version

    @staticmethod
    def get_sheet_name():
        return sheet_retirement

class Retirement(Model, DataTableMixin):
    __tablename__ = "Retirement"
    id = Column(Integer, primary_key=True, autoincrement=True)
    DUID = Column(String(50))
    State = Column(String(10))
    Registered_Capacity = Column(DECIMAL(32,16))
    Impact_To_State = Column(String(10))
    Adjustment_Factor = Column(DECIMAL(7,6))
    Closure_Date = Column(Date)
    Back_To_Service_Date = Column(Date)
    Version = Column(Integer,
                            ForeignKey('Retirement_Definition.Retirement_Version'),
                            nullable=False)
    Retirement_Definition = relationship('RetirementDefinition',
                                    foreign_keys=[Version],
                                    backref="data")
    included_keys = ['DUID','State','Registered_Capacity','Impact_To_State','Adjustment_Factor','Closure_Date','Back_To_Service_Date']
    column_type_dict = {'DUID':'string' ,'State':'string', 'Registered_Capacity': 'numeric', 'Impact_To_State': 'string',
                        'Adjustment_Factor': 'numeric', 'Closure_Date':'date', 'Back_To_Service_Date': 'date'}

"""Project List"""
class ProjectListDefinition(Model, DefTableMixin):
    __tablename__ = "Project_List_Definition"
    Project_List_Version = Column(Integer, primary_key=True, autoincrement=True)
    Note = Column(String(512))

    def get_version(self):
        return self.Project_List_Version

    @staticmethod
    def get_sheet_name():
        return sheet_project_list

class ProjectList(Model, DataTableMixin):
    __tablename__ = "Project_List"
    id = Column(Integer, primary_key=True, autoincrement=True)
    DUID = Column(String(50))
    Name = Column(String(50))
    State = Column(String(10))
    Fuel_Type = Column(String(10))
    Start_Date = Column(Date)
    End_Date = Column(Date)
    Status = Column(String(50))
    Offer_Rate = Column(DECIMAL(32,16))
    Maximum_Quantity = Column(DECIMAL(32,16))
    Installed_Quantity = Column(DECIMAL(32,16))
    Probability_Of_Success = Column(DECIMAL(5,4))
    Resolution = Column(String(20))
    Proxy = Column(String(50))
    Version = Column(Integer,
                            ForeignKey('Project_List_Definition.Project_List_Version'),
                            nullable=False)
    Project_List_Definition = relationship('ProjectListDefinition',
                                    foreign_keys=[Version],
                                    backref="data")
    included_keys = ['DUID','Name','State','Fuel_Type','Start_Date','End_Date','Status','Offer_Rate','Maximum_Quantity',
                     'Installed_Quantity','Probability_Of_Success','Resolution','Proxy']
    column_type_dict = {'DUID':'string', 'Name':'string','State':'string','Fuel_Type':'string', 'Start_Date':'date',
                        'End_Date':'date', 'Status':'string', 'Offer_Rate':'numeric', 'Maximum_Quantity': 'numeric',
                        'Installed_Quantity':'numeric', 'Probability_Of_Success':'numeric', 'Resolution':'string',
                        'Proxy':'string'}


model_list = {
    ('RooftopSolarHistoryDefinition', 'RooftopSolarHistory'),
    ('RooftopSolarForecastDefinition', 'RooftopSolarForecast'),
    ('RenewableProportionDefinition', 'RenewableProportion'),
    ('DemandGrowthDefinition', 'DemandGrowth'),
    ('BehindTheMeterBatteryDefinition', 'BehindTheMeterBattery'),
    ('ProjectProxyDefinition', 'ProjectProxy'),
    ('MPCCPTDefinition', 'MPCCPT'),
    ('GasPriceEscalationDefinition', 'GasPriceEscalation'),
    ('StrategicBehaviourDefinition', 'StrategicBehaviour'),
    ('RetirementDefinition', 'Retirement'),
    ('ProjectListDefinition', 'ProjectList')
}

def find_table_class_by_name(name):
    import sys
    return getattr(sys.modules[__name__], name)

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