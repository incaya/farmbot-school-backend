#!/usr/bin/python
#coding: utf-8

import json

from flask import jsonify, request, make_response 
from flask_restful import Resource

from sqlalchemy.exc import SQLAlchemyError

from utils.jwt import jwt_needed, admin_required

from werkzeug.security import generate_password_hash

from db import conn
from db.models import User as UserModel

from utils.resource import init_reqparser, query_apply_reqparser
from utils.sanitizers import check_data
from utils.utils import contains

db = conn.db

model = UserModel()
parser = init_reqparser()

def bulkPost(userList):
    result = []
    for u in userList:
        
        data = check_data(model, json.dumps(u))

        user = UserModel(**data) 
        
        db.session.add(user)
        try:
            db.session.commit()
        except:
            db.session.rollback()
        else:
            result.append({
                "id": user.id,
                'pseudo': user.pseudo, 
                'name' : user.name, 
                'email' : user.email, 
                'group_id' : user.group_id, 
                'role' : {
                    "code": user.role.name,
                    "label": user.role.value
                },
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': user.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })

    return result

class Users(Resource):
    @admin_required
    @jwt_needed
    def get(self):
        """
        Lister tous les comptes
        ---
        tags: 
            - Gestion des comptes
        parameters:
            - in: query
              name: sort
              type: string
              description: Examples = sort=end_date (sort by end_date ascending) ; sort=-end_date (sort by end_date descending)
            - in: query
              name: offset
              type: integer
              description: The number of items to skip before starting to collect the result set
            - in: query
              name: limit
              type: integer
              description: The numbers of items to return
        responses:
            200:
                description: A list of users
                schema:
                    type: array
                    "$ref": "#/definitions/user"
        """
        parser.add_argument('role', type=str, help='Roles available `ADMIN` `USER`')
        args = parser.parse_args()
        users =  model.query

        role = args['role']
        if role and contains(role, ['ADMIN', 'USER']):
            users = users.filter_by(role=role)

        users = query_apply_reqparser(UserModel, users, args)
        users = users.all()
        output = [] 
        for user in users: 
            sequences = []
            [sequences.append(s.as_dict(unloaded_fields=['user_id'])) for s in user.sequences]
            output.append({ 
                'id': user.id,
                'pseudo': user.pseudo, 
                'name' : user.name, 
                'email' : user.email, 
                'group_id' : user.group_id, 
                'role' : {
                    "code": user.role.name,
                    "label": user.role.value
                },
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': user.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'sequences' : sequences
            }) 

        return make_response(jsonify({'users': output}), 200)

    @admin_required
    @jwt_needed
    def post(self):
        """
        Créer un compte
        ---
        tags: 
            - Gestion des comptes
        parameters:
            - in: body
              name: body
              required: true
              schema:
                required:
                    - email
                    - password
                    - pseudo
                    - role
                properties:
                    email:
                        type: string
                        format: email
                        description: account email
                    password:
                        type: string
                        format: password
                        description: account password
                    pseudo:
                        type: string
                        description: account pseudo
                    name:
                        type: string
                        description: user name
                    role:
                        type: string
                        description: user role
                        enum: ['Administrateur', 'Utilisateur']
        responses:
            200:
                description: created user
                schema:
                    type: array
                    "$ref": "#/definitions/user"
            202:
                description: user email or name already exists
            400:
                description: wrong body content
        """
        data = check_data(model, request.data)

        if 'error' in data:
            return make_response(data, 400)

        if 'password' not in data:
            return {"error": { "message": "error in request data", "missing_field": "password" }}

        if 'role' not in data:
            return {"error": { "message": "error in request data", "missing_field": "role" }}

        data['password'] = generate_password_hash(data['password'])

        user = model.query\
            .filter_by(email = data['email'])\
            .first() 
        if not user: 
            user = UserModel(**data) 
            
            db.session.add(user)
            try:
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
                    "id": user.id,
                    'pseudo': user.pseudo, 
                    'name' : user.name, 
                    'email' : user.email, 
                    'group_id' : user.group_id, 
                    'role' : {
                        "code": user.role.name,
                        "label": user.role.value
                    },
                    'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': user.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                }), 200)
        else: 
            return make_response('User already exists. Please Log in.', 202)

class User(Resource):  
    @admin_required
    @jwt_needed
    def get(self, id):
        """
        Rechercher un compte
        ---
        tags: 
            - Gestion des comptes
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: user id
        responses:
            200:
                description: A user account
                schema:
                    type: object
                    "$ref": "#/definitions/user"
            404:
                description: user id not found
        """
        user = model.query.get(id)
        
        if not user:
            return make_response( 
                'User not found', 
                404
            ) 
        else:
            sequences = []
            [sequences.append(s.as_dict(unloaded_fields=['user_id'])) for s in user.sequences]
            return make_response(jsonify({
                'id': user.id,
                'pseudo': user.pseudo, 
                'name' : user.name, 
                'email' : user.email, 
                'group_id' : user.group_id, 
                'role' : {
                    "code": user.role.name,
                    "label": user.role.value
                },
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': user.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'sequences' : sequences
            }), 200)
    
    @admin_required
    @jwt_needed
    def put(self, id):
        """
        Modifier un compte
        ---
        tags: 
            - Gestion des comptes
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: user id
            - in: body
              name: body
              required: true
              schema:
                required:
                    - email
                    - pseudo
                properties:
                    email:
                        type: string
                        format: email
                        description: account email
                    pseudo:
                        type: string
                        description: account pseudo
                    name:
                        type: string
                        description: user name
        responses:
            200:
                description: updated user
                schema:
                    type: object
                    "$ref": "#/definitions/user"
            400:
                description: wrong body content
            404:
                description: user id not found
        """
        user = model.query.get(id)
        
        if not user:
            return make_response( 
                'User not found', 
                404
            ) 
        else:
            data = check_data(model, request.data)

            if 'error' in data:
                return make_response(data, 400)

            user.pseudo = data['pseudo']
            user.name = data['name']
            user.email = data['email']
            user.group_id = data['group_id']
            user.created_at = user.created_at
            user.updated_at = data['updated_at']
            try:
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
                sequences = []
                [sequences.append(s.as_dict(unloaded_fields=['user_id'])) for s in user.sequences]
                return make_response(jsonify({
                    'id': user.id,
                    'pseudo': user.pseudo, 
                    'name' : user.name, 
                    'email' : user.email, 
                    'group_id' : user.group_id, 
                    'role' : {
                        "code": user.role.name,
                        "label": user.role.value
                    },
                    'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': user.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'sequences' : sequences
                }), 200)

    @admin_required
    @jwt_needed
    def delete(self, id):
        """
        Supprimer un compte
        ---
        tags: 
            - Gestion des comptes
        parameters:
            - in: path
              name: id
              required: true
              description: user id
        responses:
            200:
                description: user deleted
            404:
                description: user id not found
        """
        user = model.query.get(id)
        if not user: 
            return make_response( 
                'User not found', 
                404
            )
        else:
            db.session.delete(user) 
            db.session.commit()
            return make_response( 
                'User deleted', 
                200
            )