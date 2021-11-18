#!/usr/bin/python
#coding: utf-8

from sqlalchemy.dialects.postgresql import UUID, JSONB
from enum import Enum
import uuid, datetime

from utils.model import is_mandatory, mandatory_fields, not_allow_empty_fields, as_dict as model_as_dict

from db import conn

db = conn.db

class SequenceStatus(Enum):
    WIP = "En cours"
    TO_PROCESS = "A traiter"
    PROCESS_WIP = "Validation en cours"
    PROCESSED = "Traité"

class Sequence(db.Model):
    field_list = {
        'user_id': {
            'mandatory': True
        },
        'challenge_id': {
            'mandatory': True
        },
        'status': {
            'mandatory': True
        },
        "actions": {
            'mandatory': False
        },
        "fb_seq_id": {
            'mandatory': False
        },
        "comments": {
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
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=not is_mandatory(field_list, 'user_id'))
    challenge_id = db.Column(UUID(as_uuid=True), db.ForeignKey('challenge.id'), nullable=not is_mandatory(field_list, 'challenge_id'))
    status = db.Column(db.Enum(SequenceStatus), nullable=not is_mandatory(field_list, 'status'))
    actions = db.Column(JSONB(),  nullable=not is_mandatory(field_list, 'actions'))
    fb_seq_id = db.Column(db.SMALLINT(), nullable=not is_mandatory(field_list, 'fb_seq_id'))
    comments = db.Column(JSONB(),  nullable=not is_mandatory(field_list, 'comments'))
    created_at = db.Column(db.DateTime, nullable=not is_mandatory(field_list, 'created_at'), default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=not is_mandatory(field_list, 'updated_at'), default=datetime.datetime.utcnow)
    user = db.relationship("User", back_populates="sequences")
    
    def __init__(self, **kwargs):
        self.user_id = kwargs.get('user_id', None)
        self.challenge_id = kwargs.get('challenge_id', None)
        self.status = kwargs.get('status', None)
        self.actions = kwargs.get('actions', [])
        self.fb_seq_id = kwargs.get('fb_seq_id', None)
        self.comments = kwargs.get('comments', [])
        self.created_at = kwargs.get('created_at', datetime.datetime.utcnow)
        self.updated_at = kwargs.get('updated_at', datetime.datetime.utcnow)
        self.fields = self.field_list
        self.mandatory = mandatory_fields(self.field_list)
        self.not_allow_empty = not_allow_empty_fields(self.field_list)

    def as_dict(self, **kwargs):
        result = model_as_dict(self, **dict(kwargs, special_fields={'status': 'enum'}))
        result['user'] = model_as_dict(self.user, unloaded_fields=['password', 'role'], special_fields={'role': 'enum'})
        return result
