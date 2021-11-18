#!/usr/bin/python
#coding: utf-8

from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid, datetime

from utils.model import is_mandatory, mandatory_fields, not_allow_empty_fields, as_dict as model_as_dict

from db import conn

db = conn.db

class Challenge(db.Model):
    field_list = {
        'title': {
            'mandatory': True
        },
        'end_date': {
            'mandatory': True
        },
        'description': {
            'mandatory': False,
            'allow_empty': True
        },
        'active': {
            'mandatory': True
        },
        'group_id': {
            'mandatory': False
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
    title = db.Column(db.String(255), nullable=not is_mandatory(field_list, 'title'), unique=True)
    end_date = db.Column(db.DateTime, nullable=not is_mandatory(field_list, 'end_date'))
    description = db.Column(db.String, nullable=not is_mandatory(field_list, 'description'))
    active = db.Column(db.Boolean, nullable=not is_mandatory(field_list, 'active', ), default=0)
    group_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user_group.id'), nullable=not is_mandatory(field_list, 'group_id'))
    created_at = db.Column(db.DateTime, nullable=not is_mandatory(field_list, 'created_at'), default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=not is_mandatory(field_list, 'updated_at'), default=datetime.datetime.utcnow)
    sequences = db.relationship("Sequence", backref="challenge")

    def __init__(self, **kwargs):
        self.title = kwargs.get('title', None)
        self.end_date = kwargs.get('end_date', None)
        self.description = kwargs.get('description', None)
        self.active = kwargs.get('active', None)
        self.group_id = kwargs.get('group_id', None)
        self.created_at = kwargs.get('created_at', datetime.datetime.utcnow)
        self.updated_at = kwargs.get('updated_at', datetime.datetime.utcnow)
        self.sequences = kwargs.get('sequences', [])
        self.fields = self.field_list
        self.mandatory = mandatory_fields(self.field_list)
        self.not_allow_empty = not_allow_empty_fields(self.field_list)

    def as_dict(self, **kwargs):
        return model_as_dict(self, **dict(kwargs, special_fields={'end_date':'date'}))
