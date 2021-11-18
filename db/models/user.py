#!/usr/bin/python
#coding: utf-8

from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
import uuid, datetime

from utils.model import is_mandatory, mandatory_fields, not_allow_empty_fields, as_dict as model_as_dict

from db import conn

db = conn.db

class UserRoles(Enum):
    ADMIN = "Administrateur"
    USER = "Utilisateur"

class User(db.Model):
    field_list = {
        'pseudo': {
            'mandatory': True
        },
        'name': {},
        'email': {
            'mandatory': True
        },
        'password': {
        },
        'role': {
        },
        'group_id': {
        },
        'created_at': {
            'mandatory': True
        },
        'updated_at': {
            'mandatory': True
        }
    } 

    mandatory = []

    id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    pseudo = db.Column(db.String(64), nullable=not is_mandatory(field_list, 'pseudo'), unique=True)
    name = db.Column(db.String(128), nullable=not is_mandatory(field_list, 'name'))
    email = db.Column(db.String(128), nullable=not is_mandatory(field_list, 'email'), unique=True)
    password = db.Column(db.String(128), nullable=not is_mandatory(field_list, 'password'))
    role = db.Column(db.Enum(UserRoles), nullable=not is_mandatory(field_list, 'role'))
    group_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user_group.id'), nullable=not is_mandatory(field_list, 'group_id'))
    created_at = db.Column(db.DateTime, nullable=not is_mandatory(field_list, 'created_at'), default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=not is_mandatory(field_list, 'updated_at'), default=datetime.datetime.utcnow)
    sequences = db.relationship("Sequence", back_populates="user")
   
    def __init__(self, **kwargs):
        self.pseudo = kwargs.get('pseudo', None)
        self.name = kwargs.get('name', None)
        self.email = kwargs.get('email', None)
        self.password = kwargs.get('password', None)
        self.role = kwargs.get('role', None)
        self.group_id = kwargs.get('group_id', None)
        self.created_at = kwargs.get('created_at', datetime.datetime.utcnow)
        self.updated_at = kwargs.get('updated_at', datetime.datetime.utcnow)
        self.sequences = kwargs.get('sequences', [])
        self.fields = self.field_list
        self.mandatory = mandatory_fields(self.field_list)
        self.not_allow_empty = not_allow_empty_fields(self.field_list)

    def as_dict(self, **kwargs):
        result = model_as_dict(self, unloaded_fields=['password'], special_fields={'role': 'enum'})
        return result
