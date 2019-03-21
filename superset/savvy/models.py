from datetime import timedelta
import datetime

from flask_appbuilder import Model
from sqlalchemy import (
    Boolean, Column, DateTime, Integer, Float, String, UniqueConstraint, ForeignKey, Sequence, Table)
from sqlalchemy.orm import relationship

metadata = Model.metadata  # pylint: disable=no-member
register_valid_hours = 24

assoc_org_user = Table(
    'org_user', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('ab_user.id')),
    Column('org_id', Integer, ForeignKey('organizations.id')),
    UniqueConstraint('user_id', 'org_id')
)


class Organization(Model):
    __tablename__ = 'organizations'
    id = Column(Integer, primary_key=True)
    organization_name = Column(String(250))
    users = relationship('User', secondary=assoc_org_user, backref='organization')
    superuser_number = Column('superuser_number', Integer, default=0)


class OrgRegisterUser(Model):
    """ the register model for users who are invited by admin """
    __tablename__ = 'ab_register_user'
    id = Column(Integer, Sequence('ab_register_user_id_seq'), primary_key=True)
    username = Column(String(64))
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    password = Column(String(256))
    email = Column(String(64), nullable=False)
    registration_date = Column(DateTime, default=datetime.datetime.now, nullable=True)
    registration_hash = Column(String(256))
    organization = Column(String(250), nullable=False)
    inviter = Column('inviter_id', Integer, ForeignKey('ab_user.id'), nullable=True)
    valid_date = Column(DateTime, default=(datetime.datetime.now() + timedelta(hours=register_valid_hours)),
                        nullable=True)
    role_assigned = Column('role_id', Integer, ForeignKey('ab_role.id'), nullable=True)


class ResetRequest(Model):
    ___tablename__ = 'reset_request'
    id = Column(Integer, Sequence('reset_request_id_seq'), primary_key=True)
    user_id = Column(Integer, ForeignKey('ab_user.id'))
    email = Column(String(64), nullable=False)
    reset_date = Column(DateTime, default=datetime.datetime.now, nullable=True)
    reset_hash = Column(String(256))
    used = Column(Boolean)


assoc_group_site = Table(
    'group_site', metadata,
    Column('id', Integer, primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id')),
    Column('site_id', Integer, ForeignKey('sites_data.SiteID'))
)

assoc_group_user = Table(
    'group_user', metadata,
    Column('id', Integer, primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id')),
    Column('user_id', Integer, ForeignKey('ab_user.id'))
)


class Group(Model):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    group_name = Column(String(64), nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    sites = relationship('Site',
                         secondary=assoc_group_site)
    users = relationship('User',
                         secondary=assoc_group_user)


class Site(Model):
    __tablename__ = 'sites_data'
    SiteID = Column(Integer, primary_key=True)
    SiteName = Column(String(64))
    ClientID = Column(Integer)
    ClientName = Column(String(64))
    latitude = Column(Float)
    longitude = Column(Float)
    AddressLine = Column(String(64))
    city = Column(String(64))
    State = Column(String(16))
    PostalCode = Column(Integer)
    Country = Column(String(64))



