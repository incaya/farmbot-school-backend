#!/usr/bin/python
#coding: utf-8

import json
import uuid

from flask import jsonify, request, make_response 
from flask_restful import Resource, reqparse

from sqlalchemy.exc import SQLAlchemyError

from utils.jwt import admin_required, jwt_needed, token_identity

from werkzeug.security import generate_password_hash

from db import conn
from db.models import UserGroup as UserGroupModel
from db.models import User as UserModel, UserRoles

from utils.resource import init_reqparser, query_apply_reqparser
from utils.sanitizers import check_data
from utils.utils import contains

from resources.user import bulkPost as userBulkPost

db = conn.db

model = UserGroupModel()
parser = init_reqparser()

def generateUsers(group_id, userNb):
    if not userNb:
        return []
    else:
        result = []
        for i in range(0, userNb):
            name = str(uuid.uuid4())[:8]
            result.append({
                "name": name,
                "email": name,
                "pseudo": name,
                "password": generate_password_hash(name),
                "role": 'USER',
                "group_id": group_id
            })

        return userBulkPost(result)

class UserGroups(Resource):
    @jwt_needed
    def get(self):
        """
        Lister tous les groupes d'utilisateurs
        ---
        tags: 
            - Gestion des comptes
        parameters:
            - in: query
              name: sort
              type: string
              description: Examples = sort=name (sort by end_date ascending) ; sort=-name (sort by end_date descending)
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
                description: A list of users groups
                schema:
                    type: array
                    $ref: '#/definitions/usergroup'
        """
        args = parser.parse_args()

        usergroups = model.query
          
        usergroups = query_apply_reqparser(UserGroupModel, usergroups, args)
        usergroups = usergroups.all()

        output = [] 

        for usergroup in usergroups:
            users = []
            [users.append(s.as_dict(unloaded_fields=['group_id'])) for s in usergroup.users]
            challenges = []
            [challenges.append(s.as_dict(unloaded_fields=['group_id'])) for s in usergroup.challenges]
            output.append({ 
                'id': usergroup.id,
                'name': usergroup.name,
                'created_at': usergroup.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': usergroup.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'users': users,
                'challenges': challenges
            })

        return make_response(jsonify({'usergroups': output}), 200)

    @admin_required
    @jwt_needed
    def post(self):
        """
        Créer un groupe d'utilisateurs
        ---
        tags: 
            - Gestion des comptes
        parameters:
            - in: body
              name: body
              required: true
              schema:
                required:
                    - name
                properties:
                    name:
                        type: string
                        description: UserGroup name
 
        responses:
            200:
                description: A list of groups
                schema:
                    type: array
                    $ref: '#/definitions/usergroup'
            202:
                description: group name already exists
            400:
                description: wrong body content
         """
        data = check_data(model, request.data)
        
        if 'error' in data:
            return make_response(data, 400)

        nbOfUserToGenerate = 0
        if 'generate_learners' in data:
            nbOfUserToGenerate = int(data['generate_learners'])
        if 'generateLearners' in data:
            nbOfUserToGenerate = int(data['generateLearners'])

        usergroup = model.query\
            .filter_by(name = data['name'])\
            .first() 
        if not usergroup: 
            usergroup = UserGroupModel(**data) 
            try:
                db.session.add(usergroup) 
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
                users = generateUsers(str(usergroup.id), nbOfUserToGenerate)
                return make_response(jsonify({
                    "id": usergroup.id,
                    "name": usergroup.name,
                    "created_at": usergroup.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "updated_at": usergroup.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "users": users,
                    "challenges": []
                }), 200)
        else: 
            return make_response('UserGroup name already exists', 202)

class UserGroup(Resource):
    @jwt_needed
    def get(self, id):
        """
        Rechercher un groupe d'utilisateur
        ---
        tags: 
            - Gestion des comptes
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: usergroup id
        responses:
            200:
                description: A User Group
                schema:
                    type: object
                    $ref: '#/definitions/usergroup'
        """
        usergroup = model.query.get(id)
        
        if not usergroup:
            return make_response( 
                'UserGroup not found', 
                404
            ) 
        else:
            users = []
            [users.append(s.as_dict(unloaded_fields=['group_id'])) for s in usergroup.users]
            challenges = []
            [challenges.append(s.as_dict(unloaded_fields=['group_id'])) for s in usergroup.challenges]
            return make_response(jsonify({
                'id': usergroup.id,
                'name': usergroup.name,
                'created_at': usergroup.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': usergroup.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'users' : users,
                'challenges': challenges
            }), 200)

    @admin_required
    @jwt_needed
    def put(self, id):
        """
        Modifier un groupe d'utilisateur
        ---
        tags: 
            - Gestion des comptes
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: group id
            - in: body
              name: body
              required: true
              schema:
                required:
                    - name
                properties:
                    name:
                        type: string
                        description: UserGroup name
        responses:
            200:
                description: A user group
                schema:
                    type: object
                    $ref: '#/definitions/usergroup'
            404:
                description: UserGroup not found
            400:
                description: wrong body content
        """
        usergroup = model.query.get(id)
        
        if not usergroup:
            return make_response( 
                'UserGroup not found', 
                404
            ) 
        else:
            data = check_data(model, request.data, to_update=True)

            if 'error' in data:
                return make_response(data, 400)

            try:
                usergroup.name = data['name']
                usergroup.created_at = usergroup.created_at
                usergroup.updated_at = data['updated_at']
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
                users = []
                [users.append(s.as_dict(unloaded_fields=['group_id'])) for s in usergroup.users]
                challenges = []
                [challenges.append(s.as_dict(unloaded_fields=['group_id'])) for s in usergroup.challenges]
                return make_response(jsonify({
                    'name': usergroup.name,
                    'created_at': usergroup.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': usergroup.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'users': users,
                    'challenges': challenges
                }), 200)
    
    @admin_required
    @jwt_needed
    def delete(self, id):
        """
        Supprimer un groupe d'utilisateurs
        ---
        tags: 
            - Gestion des comptes
        parameters:
            - in: path
              name: id
              required: true
              description: usergroup id
        responses:
            200:
                description: usergroup deleted
            404:
                description: usergroup id not found
        """
        usergroup = model.query.get(id)
        if not usergroup: 
            return make_response( 
                'UserGroup not found', 
                404
            )
        else:
            db.session.delete(usergroup) 
            db.session.commit()
            return make_response( 
                'UserGroup deleted', 
                200
            )
