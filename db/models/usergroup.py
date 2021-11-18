#!/usr/bin/python
#coding: utf-8

from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
import uuid

from utils.model import is_mandatory, mandatory_fields, not_allow_empty_fields, as_dict as model_as_dict

from db import conn

db = conn.db

class UserGroup(db.Model):
    field_list = {
        'name': {
            'mandatory': True
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
    name = db.Column(db.String(128), nullable=not is_mandatory(field_list, 'name'), unique=True)
    users = db.relationship("User", backref="usergroup")
    challenges = db.relationship("Challenge", backref="usergroup")
    created_at = db.Column(db.DateTime, nullable=not is_mandatory(field_list, 'created_at'))
    updated_at = db.Column(db.DateTime, nullable=not is_mandatory(field_list, 'updated_at'))
    
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', None)
        self.created_at = kwargs.get('created_at', None)
        self.updated_at = kwargs.get('updated_at', None)
        self.users = kwargs.get('users', [])
        self.challenges = kwargs.get('challenges', [])
        self.fields = self.field_list
        self.mandatory = mandatory_fields(self.field_list)
        self.not_allow_empty = not_allow_empty_fields(self.field_list)

    def as_dict(self, **kwargs):
        result = model_as_dict(self)
        return result
