#!/usr/bin/python
#coding: utf-8

import json

from flask import jsonify, request, make_response 
from flask_restful import Resource, reqparse

from sqlalchemy.exc import SQLAlchemyError

from utils.jwt import admin_required, jwt_needed, token_identity, token_role, token_group

from werkzeug.security import generate_password_hash

from db import conn
from db.models import Challenge as ChallengeModel

from utils.resource import init_reqparser, query_apply_reqparser
from utils.sanitizers import check_data
from utils.utils import contains

db = conn.db

model = ChallengeModel()
parser = init_reqparser()

def check_user_seq(sequences):
    if sequences:
        for s in sequences:
            if str(s['user_id']) == str(token_identity()):
                return s['id']
    return None

class Challenges(Resource):
    @jwt_needed
    def get(self):
        """
        Lister tous les défis
        ---
        tags: 
            - Défis
        parameters:
            - in: query
              name: active
              type: string
              description: true or false to get only active or inactive challenges
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
                description: A list of challenges
                schema:
                    type: array
                    $ref: '#/definitions/challenge'
        """
        parser.add_argument('active', type=str, help='Active accept two values `true` or `false`')
        args = parser.parse_args()

        challenges = model.query

        active = args['active']
        if active and contains(active, ['true','false']):
            challenges = challenges.filter_by(active=active)

        if token_role() != 'Administrateur':
            challenges = challenges.filter_by(group_id=token_group())

        challenges = query_apply_reqparser(ChallengeModel, challenges, args)
        challenges = challenges.all()

        output = [] 

        for challenge in challenges:
            sequences = []
            [sequences.append(s.as_dict(unloaded_fields=['challenge_id'])) for s in challenge.sequences]
            output.append({ 
                'id': challenge.id,
                'title': challenge.title, 
                'end_date': challenge.end_date.strftime('%Y-%m-%d') if challenge.end_date else None, 
                'description': challenge.description, 
                'active': challenge.active,
                'group_id': challenge.group_id,
                'sequences': sequences,
                'created_at': challenge.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': challenge.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'user_seq': check_user_seq(sequences)
            })

        return make_response(jsonify({'challenges': output}), 200)

    @admin_required
    @jwt_needed
    def post(self):
        """
        Créer un défi
        ---
        tags: 
            - Défis
        parameters:
            - in: body
              name: body
              required: true
              schema:
                required:
                    - title
                    - end_date
                    - active
                properties:
                    title:
                        type: string
                        description: Challenge title
                    end_date:
                        type: string
                        format: date
                        description: Challenge end date
                    description:
                        type: string
                        description: Challenge description
                    active:
                        type: boolean
                        description: Challenge activation flag
                    group_id:
                        type: string
                        format: uuid
                        description: User Group id
 
        responses:
            200:
                description: A list of challenges
                schema:
                    type: array
                    $ref: '#/definitions/challenge'
            202:
                description: challenge title already exists
            400:
                description: wrong body content
         """
        
        data = check_data(model, request.data)

        if 'error' in data:
            return make_response(data, 400)

        challenge = model.query\
            .filter_by(title = data['title'])\
            .first() 
        if not challenge: 
            challenge = ChallengeModel(**data) 
            try:
                db.session.add(challenge) 
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
                    "id": challenge.id,
                    'title': challenge.title, 
                    'end_date': challenge.end_date.strftime('%Y-%m-%d') if challenge.end_date else None, 
                    'description': challenge.description, 
                    'active': challenge.active,
                    'group_id': challenge.group_id,
                    'created_at': challenge.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': challenge.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                }), 200)
        else: 
            return make_response('Challenge title already exists', 202)

class Challenge(Resource):  
    @jwt_needed
    def get(self, id):
        """
        Rechercher un défi
        ---
        tags: 
            - Défis
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: challenge id
        responses:
            200:
                description: A challenge
                schema:
                    type: object
                    $ref: '#/definitions/challenge'
        """
        challenge = model.query.get(id)
        
        if not challenge:
            return make_response( 
                'Challenge not found', 
                404
            ) 
        else:
            sequences = []
            [sequences.append(s.as_dict(unloaded_fields=['challenge_id'])) for s in challenge.sequences]
            return make_response(jsonify({
                'id': challenge.id,
                'title': challenge.title, 
                'end_date' : challenge.end_date.strftime('%Y-%m-%d') if challenge.end_date else None, 
                'description': challenge.description, 
                'active' : challenge.active,
                'group_id': challenge.group_id,
                'sequences' : sequences,
                'user_seq': check_user_seq(sequences),
                'created_at': challenge.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': challenge.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }), 200)

    @admin_required
    @jwt_needed
    def put(self, id):
        """
        Modifier un défi
        ---
        tags: 
            - Défis
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: challenge id
            - in: body
              name: body
              required: true
              schema:
                required:
                    - title
                    - end_date
                    - description
                    - active
                    - group_id
                properties:
                    title:
                        type: string
                        description: Challenge title
                    end_date:
                        type: string
                        format: date
                        description: Challenge end date
                    description:
                        type: string
                        description: Challenge description
                    active:
                        type: boolean
                        description: Challenge activation flag
                    group_id:
                        type: string
                        format: uuid
                        description: User Group id
        responses:
            200:
                description: A challenge
                schema:
                    type: object
                    $ref: '#/definitions/challenge'
            400:
                description: wrong body content
        """
        challenge = model.query.get(id)
        
        if not challenge:
            return make_response( 
                'Challenge not found', 
                404
            ) 
        else:
            data = check_data(model, request.data)

            if 'error' in data:
                return make_response(data, 400)

            try:
                challenge.title = data['title']
                challenge.end_date = data['end_date']
                challenge.description = data['description']
                challenge.group_id = data['group_id']
                challenge.active = data['active']
                challenge.created_at = challenge.created_at
                challenge.updated_at = data['updated_at']
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
                    'title': challenge.title, 
                    'end_date' : challenge.end_date.strftime('%Y-%m-%d') if challenge.end_date else None,
                    'description': challenge.description,
                    'group_id': challenge.group_id, 
                    'active' : challenge.active,
                    'created_at': challenge.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': challenge.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                }), 200)
    
    @admin_required
    @jwt_needed
    def delete(self, id):
        """
        Supprimer un défi
        ---
        tags: 
            - Défis
        parameters:
            - in: path
              name: id
              required: true
              description: challenge id
        responses:
            200:
                description: challenge deleted
            404:
                description: challenge id not found
        """
        challenge = model.query.get(id)
        if not challenge: 
            return make_response( 
                'Challenge not found', 
                404
            )
        else:
            db.session.delete(challenge) 
            db.session.commit()
            return make_response( 
                'Challenge deleted', 
                200
            )
