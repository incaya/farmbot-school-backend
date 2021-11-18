#!/usr/bin/python
#coding: utf-8

import json

from flask import jsonify, request, make_response 
from flask_restful import Resource, reqparse

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from utils.jwt import admin_required, jwt_needed, token_identity

from werkzeug.security import generate_password_hash

from db import conn
from db.models import Pin as PinModel, MaterialTypes

from utils.resource import init_reqparser, query_apply_reqparser
from utils.sanitizers import check_data
from utils.utils import contains

db = conn.db

model = PinModel()
parser = init_reqparser()

def getPinByAction(action):
    pin = model.query\
        .filter_by(action = action)\
        .first()

    if not pin:
        return False

    return pin

class Pins(Resource):
    @jwt_needed
    def get(self):
        """
        Lister les actions liées à des pins
        ---
        tags: 
            - Paramétrage
        responses:
            200:
                description: A list of pin actions
                schema:
                    type: array
                    $ref: '#/definitions/pin'
        """
        pins = model.query
        pins = pins.all()

        output = [] 

        for pin in pins:
            output.append({ 
                'id': pin.id,
                'material_type': {
                    "code": pin.material_type.name,
                    "label": pin.material_type.value
                }, 
                'material_id': pin.material_id, 
                'action': pin.action,
                'created_at': pin.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': pin.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        return make_response(jsonify({'pins': output}), 200)

    @admin_required
    @jwt_needed
    def post(self):
        """
        Créer une action liée à un pin
        ---
        tags: 
            - Paramétrage
        parameters:
            - in: body
              name: body
              required: true
              schema:
                type: object
                required:
                    - material_type
                    - material_id
                    - action
                properties:
                    material_type:
                        type: string,
                        description: Material type
                        enum: ['PERIPHERAL', 'SENSOR']
                    material_id:
                        type: integer
                        description: Pin number
                    action:
                        type: string
                        description: Action related to pin
        responses:
            200:
                description: A list of pins config
                schema:
                    type: array
                    $ref: '#/definitions/pin'
            202:
                description: pin already exists
            400:
                description: wrong body content
         """
        
        data = check_data(model, request.data, enum=['material_type', MaterialTypes])

        if 'error' in data:
            return make_response(data, 400)

        pin = model.query\
            .filter(or_(
                PinModel.material_id == data['material_id'],
                PinModel.action == data['action']
            ))\
            .first()
 
        if not pin: 
            pin = PinModel(**data) 
            try:
                db.session.add(pin) 
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                return make_response(jsonify({
                    "error": {
                        "message": "unable to insert data",
                        "db error" : str(e)
                    }
                }), 400)
            else:
                return make_response(jsonify({
                    "id": pin.id,
                    'material_type': {
                        "code": pin.material_type.name,
                        "label": pin.material_type.value
                    }, 
                    'material_id': pin.material_id, 
                    'action': pin.action,
                    'created_at': pin.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': pin.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                }), 200)
        else: 
            return make_response('Pin already exists, please verify label, number or action', 202)

class Pin(Resource):  
    @jwt_needed
    def get(self, id):
        """
        Rechercher une action lié à un pin
        ---
        tags: 
            - Paramétrage
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: pin config id
        responses:
            200:
                description: A pin config
                schema:
                    type: object
                    $ref: '#/definitions/pin'
        """
        pin = model.query.get(id)
        
        if not pin:
            return make_response( 
                'Pin not found', 
                404
            ) 
        else:
            return make_response(jsonify({
                'id': pin.id,
                'material_type': {
                    "code": pin.material_type.name,
                    "label": pin.material_type.value
                }, 
                'material_id': pin.material_id, 
                'action': pin.action,
                'created_at': pin.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': pin.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }), 200)

    @admin_required
    @jwt_needed
    def put(self, id):
        """
        Modifier une action liée à un pin
        ---
        tags: 
            - Paramétrage
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: pin id
            - in: body
              name: body
              required: true
              schema:
                type: object
                required:
                    - material_type
                    - material_id
                    - action
                properties:
                    material_type:
                        type: string,
                        description: Material type
                        enum: ['PERIPHERAL', 'SENSOR']
                    material_id:
                        type: integer
                        description: Pin number
                    action:
                        type: string
                        description: Action related to pin
        responses:
            200:
                description: A pin config
                schema:
                    type: object
                    $ref: '#/definitions/pin'
            400:
                description: wrong body content
        """
        pin = model.query.get(id)
        
        if not pin:
            return make_response( 
                'Pin not found', 
                404
            ) 
        else:
            data = check_data(model, request.data)

            if 'error' in data:
                return make_response(data, 400)

            try:
                pin.material_type = data['material_type']
                pin.material_id = data['material_id']
                pin.action = data['action']
                pin.created_at = pin.created_at
                pin.updated_at = data['updated_at']
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                return make_response(jsonify({
                    "error": {
                        "message": "unable to update data",
                        "db error" : str(e)
                    }
                }), 400)
            else:
                return make_response(jsonify({
                    "id": pin.id,
                    'material_type': {
                        "code": pin.material_type.name,
                        "label": pin.material_type.value
                    }, 
                    'material_id': pin.material_id, 
                    'action': pin.action,
                    'created_at': pin.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': pin.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                }), 200)

    @admin_required
    @jwt_needed
    def delete(self, id):
        """
        Supprimer une action liée à un pin
        ---
        tags: 
            - Paramétrage
        parameters:
            - in: path
              name: id
              required: true
              description: pin id
        responses:
            200:
                description: pin deleted
            404:
                description: pin id not found
        """
        pin = model.query.get(id)
        if not pin: 
            return make_response( 
                'Pin not found', 
                404
            )
        else:
            db.session.delete(pin) 
            db.session.commit()
            return make_response( 
                'Pin deleted', 
                200
            )
