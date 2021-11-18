#!/usr/bin/python
#coding: utf-8

from utils.model import is_mandatory, mandatory_fields

from db import conn

db = conn.db

class FarmbotConfig(db.Model):
    field_list = {
        'token': {
            'mandatory': True
        },
        'token_expires_at': {
            'mandatory': True
        }
    } 

    mandatory = []

    token = db.Column(db.String(), primary_key=True)
    token_expires_at = db.Column(db.DateTime, nullable=not is_mandatory(field_list, 'token_expires_at'))
    
    def __init__(self, **kwargs):
        self.token = kwargs.get('token', None)
        self.token_expires_at = kwargs.get('token_expires_at', None)
        self.mandatory = mandatory_fields(self.field_list)
