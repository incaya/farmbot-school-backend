#!/usr/bin/python
#coding: utf-8

from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, SMALLINT
from enum import Enum
import uuid, datetime

from utils.model import is_mandatory, mandatory_fields, not_allow_empty_fields, as_dict as model_as_dict

from db import conn

db = conn.db

class MaterialTypes(Enum):
    PERIPHERAL = "Peripheral"
    SENSOR = "Sensor"

class Pin(db.Model):
    field_list = {
        'material_type': {
            'mandatory': True
        },
        'material_id': {
            'mandatory': True
        },
        'action': {
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
    material_type = db.Column(db.Enum(MaterialTypes), nullable=not is_mandatory(field_list, 'material_type'))
    material_id = db.Column(db.SMALLINT(), nullable=not is_mandatory(field_list, 'material_id'), unique=True)
    action = db.Column(db.String(255), nullable=not is_mandatory(field_list, 'action'), unique=True)
    created_at = db.Column(db.DateTime, nullable=not is_mandatory(field_list, 'created_at'), default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=not is_mandatory(field_list, 'updated_at'), default=datetime.datetime.utcnow)

    def __init__(self, **kwargs):
        self.material_type = kwargs.get('material_type', None)
        self.material_id = kwargs.get('material_id', None)
        self.action = kwargs.get('action', None)
        self.created_at = kwargs.get('created_at', datetime.datetime.utcnow)
        self.updated_at = kwargs.get('updated_at', datetime.datetime.utcnow)
        self.fields = self.field_list
        self.mandatory = mandatory_fields(self.field_list)
        self.not_allow_empty = not_allow_empty_fields(self.field_list)

    def as_dict(self, **kwargs):
        return model_as_dict(self, **dict(kwargs))
