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


from flask_appbuilder import Model
from sqlalchemy.orm import relationship
from sqlalchemy import (Column, ForeignKey, Integer,
                        String, UniqueConstraint, Float)


class ISPCapacityDefinition(Model):
    __tablename__ = "ISP_Capacity_Definition"
    __table_args__ = (UniqueConstraint('source', 'isp_case', 'scenario'),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50))
    isp_case = Column(String(50))
    scenario = Column(String(50))
    note = Column(String(512))   

    @staticmethod
    def get_check_name():
        return 'Capacity Check'

    def __str__(self):
        return f'{self.source}-{self.isp_case}-{self.scenario}'

    def set_note(self, note):
        self.note = note

    def get_note(self):
        return self.note

    def set_scenario(self, scenario):
        self.scenario = scenario

    def get_scenario(self):
        return self.scenario

    def get_version(self):
        return self.id


class ISPCapacity(Model):
    __tablename__ = "ISP_Capacity"
    __table_args__ = (UniqueConstraint('region', 'technology',
                                       'year', 'isp_cap_def_id'),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String(50))
    technology = Column(String(50))
    year = Column(Integer)
    value = Column(Float)
    isp_cap_def_id = Column(Integer,
                            ForeignKey('ISP_Capacity_Definition.id'),
                            nullable=False)

    ISPCapacityDefinition = relationship('ISPCapacityDefinition',
                                         foreign_keys=[isp_cap_def_id],
                                         backref="data")

    def get_definition(self):
        return self.isp_cap_def

    @staticmethod
    def get_version_col_name():
        return 'isp_cap_def_id'


check_model_list = {
    ('ISPCapacityDefinition', 'ISPCapacity')
}


def find_check_table_class_by_name(name):
    import sys
    return getattr(sys.modules[__name__], name)
