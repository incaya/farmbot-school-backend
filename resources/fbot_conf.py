#!/usr/bin/python
#coding: utf-8

import config
import requests
import json
from datetime import datetime, date

from flask import jsonify, request, make_response 
from flask_restful import Resource

from sqlalchemy.exc import SQLAlchemyError

from utils.jwt import jwt_needed, admin_required

from werkzeug.security import generate_password_hash

from db import conn
from db.models import FarmbotConfig as FarmbotConfigModel

db = conn.db

model = FarmbotConfigModel()

def token_expired():
    fbot_conf = model.query.first()
    if fbot_conf:
        return fbot_conf.token_expires_at.date() < date.today()
    return True

def get_fbot_token():
    if not token_expired():
        fbot_conf = model.query.first()
        return make_response(jsonify({
            'token' : fbot_conf.token, 
            'token_expires_at' : fbot_conf.token_expires_at
        }), 200)

    # Get your FarmBot Web App token.
    headers = {'content-type': 'application/json'}
    user = {'user': {'email': config.getConfigKey('farmbot-api.email'), 'password': config.getConfigKey('farmbot-api.password')}}
    response = requests.post(config.getConfigKey('farmbot-api.url')+'/tokens',
                             headers=headers, json=user)

    response = response.json()    
    if 'token' in response:
        fbot_conf = model.query.first()
        if fbot_conf:
            db.session.delete(fbot_conf)

        fbot_conf = FarmbotConfigModel()
        fbot_conf.token = response['token']['encoded']
        fbot_conf.token_expires_at = datetime.fromtimestamp(response['token']['unencoded']['exp'])
        db.session.add(fbot_conf)
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            return make_response(jsonify({
                "message": "unable to insert data",
                "db error" : str(e)
            }), 400)
        else:
            return make_response(jsonify({
                'token' : fbot_conf.token, 
                'token_expires_at' : fbot_conf.token_expires_at
            }), 200)
    else:
        return make_response(jsonify({
                "message": "unable to get farmbot api token"
            }), 400)

def getPin(token, pType, pin_id):
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    try:
        response = requests.get(config.getConfigKey('farmbot-api.url')+'/'+str.lower(pType)+'s',
                                headers=headers)
    except Exception as e:
        return { "error" : 'config key '+str(e)+' not exists'}

    response = response.json()
    
    for r in response:
        if r['pin'] == pin_id:
            return r
    
    return None

def create_or_update_sequence(token, data, fb_seq_id):
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    try:
        if fb_seq_id:
            response = requests.put(config.getConfigKey('farmbot-api.url')+'/sequences/'+str(fb_seq_id),
                                headers=headers, json=data)
        else:
            response = requests.post(config.getConfigKey('farmbot-api.url')+'/sequences',
                                headers=headers, json=data)
    except Exception as e:
        return {
            "error": e
        }

    response = response.json()

    return response

def delete_sequence(token, fb_seq_id):
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    try:
        if fb_seq_id:
            response = requests.delete(config.getConfigKey('farmbot-api.url')+'/sequences/'+str(fb_seq_id),
                                headers=headers)
        else:
            return make_response(jsonify({
                "message": "sequence id not specified"
            }), 400)
    except Exception as e:
        return make_response(jsonify({
            "message": e
        }), 400)

    return make_response('sequence deleted on farmbot', 200)

class FarmbotConfig(Resource):  
    @admin_required
    @jwt_needed
    def post(self):   
        return get_fbot_token()
