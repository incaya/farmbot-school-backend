#!/usr/bin/python
#coding: utf-8

import json

from flask import jsonify, request, make_response 
from flask_restful import Resource

from sqlalchemy.exc import SQLAlchemyError

from utils.jwt import jwt_needed, admin_required, token_identity, token_pseudo, token_role

from db import conn
from db.models import Sequence as SequenceModel

from resources.fbot_conf import get_fbot_token, create_or_update_sequence, delete_sequence

from utils.resource import init_reqparser, query_apply_reqparser
from utils.sanitizers import check_data
from utils.utils import contains
from utils.celery import sequence_action_to_celery

db = conn.db

model = SequenceModel()
parser = init_reqparser()

class Sequences(Resource):
    @jwt_needed
    def get(self):
        """
        Lister toutes les séquences
        ---
        tags: 
            - Séquences
        parameters:
            - in: query
              name: status
              type: string
              description: status
              enum: ['WIP', 'TO_PROCESS', 'PROCESS_WIP', 'PROCESSED']
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
                description: A list of sequences
                schema:
                    type: object
                    $ref: '#/definitions/sequence'
        """
        parser.add_argument('status', type=str, help='Status available `WIP` `TO_PROCESS` `PROCESS_WIP` `PROCESSED`')
        args = parser.parse_args()
        sequences =  model.query

        status = args['status']
        if status and contains(status, ['WIP', 'TO_PROCESS', 'PROCESS_WIP', 'PROCESSED']):
            sequences = sequences.filter_by(status=status)
        
        if token_role() != 'Administrateur':
            sequences = sequences.filter(SequenceModel.user_id == token_identity())
         
        sequences = query_apply_reqparser(SequenceModel, sequences, args)
        sequences = sequences.all()

        output = [] 
        for sequence in sequences:
            output.append({ 
                'id': sequence.id,
                'user_id': sequence.user_id, 
                'challenge_id' : sequence.challenge_id, 
                'status' : {
                    "code": sequence.status.name,
                    "label": sequence.status.value
                },
                "actions": sequence.actions,
                "fb_seq_id": sequence.fb_seq_id,
                "comments": sequence.comments,
                'created_at': sequence.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': sequence.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }) 

        return make_response(jsonify({'sequences': output}), 200)

    @jwt_needed
    def post(self):
        """
        Créer une séquence
        ---
        tags: 
            - Séquences
        parameters:
            - in: body
              name: body
              required: true
              schema:
                required:
                    - user_id
                    - challenge_id
                properties:
                    challenge_id:
                        type: string
                        format: uuid
                        description: Linked challenge (id)
                    user_id:
                        type: string
                        format: uuid
                        description: Creator of the sequence (user id)
                    actions:
                        type: array
                        description: List of actions
                        items:
                            type: object
                            properties:
                                position:
                                    type: integer
                                type:
                                    type: string
                                    enum: ['find_home', 'humidity', 'move_absolute', 'move_relative', 'take_photo', 'wait', 'water']
                                param:
                                    type: object
        responses:
            200:
                description: created sequence
                schema:
                    type: array
                    $ref: '#/definitions/sequence'
            400:
                description: wrong body content
        """
        data = check_data(model, request.data, force_default={'status':'WIP'}, force_if_missing={'user_id': token_identity()})

        if 'error' in data:
            return make_response(data, 400)

        sequence = SequenceModel(**data)

        db.session.add(sequence)
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
                'id': sequence.id,
                'user_id': sequence.user_id, 
                'challenge_id' : sequence.challenge_id, 
                'status' : {
                    "code": sequence.status.name,
                    "label": sequence.status.value
                },
                "actions": sequence.actions,
                "fb_seq_id": sequence.fb_seq_id,
                "comments": sequence.comments,
                'created_at': sequence.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': sequence.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }), 200)

class Sequence(Resource):  
    @jwt_needed
    def get(self, id):
        """
        Rechercher une séquence
        ---
        tags: 
            - Séquences
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: sequence id
        responses:
            200:
                description: A sequence
                schema:
                    type: object
                    $ref: '#/definitions/sequence'
            404:
                description: sequence id not found
        """
        sequence = model.query.get(id)
        
        if (not sequence) or (str(token_role()) != 'Administrateur' and str(sequence.user_id) != str(token_identity())):
            return make_response( 
                'Sequence not found', 
                404
            ) 
        else:
            return make_response(jsonify({
                'id': sequence.id,
                'user_id': sequence.user_id,
                'user': sequence.user.as_dict(),
                'challenge' : sequence.challenge.as_dict(), 
                'status' : {
                    "code": sequence.status.name,
                    "label": sequence.status.value
                },
                "actions": sequence.actions,
                "fb_seq_id": sequence.fb_seq_id,
                "comments": sequence.comments,
                'created_at': sequence.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': sequence.updated_at.strftime('%Y-%m-%d %H:%M:%S')
           }), 200)
    
    @jwt_needed
    def put(self, id):
        """
        Modifier une séquence
        ---
        tags: 
            - Séquences
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: sequence id
            - in: body
              name: body
              required: true
              schema:
                required:
                    - user_id
                    - challenge_id
                properties:
                    challenge_id:
                        type: string
                        format: uuid
                        description: Linked challenge (id)
                    user_id:
                        type: string
                        format: uuid
                        description: Creator of the sequence (user id)
                    actions:
                        type: array
                        description: List of actions
                        items:
                            type: object
                            properties:
                                position:
                                    type: integer
                                type:
                                    type: string
                                    enum: ['find_home', 'humidity', 'move_absolute', 'move_relative', 'take_photo', 'wait', 'water']
                                param:
                                    type: object
                    comments:
                        type: array
                        description: List of user cemments
                        items:
                            schema:
                                #ref": "#/definitions/sequence_comment
        responses:
            200:
                description: updated sequence
                schema:
                    type: array
                    $ref: '#/definitions/sequence'
            400:
                description: wrong body content
            404:
                description: sequence id not found
        """
        sequence = model.query.get(id)
        
        if (not sequence) or (str(token_role()) != 'Administrateur' and str(sequence.user_id) != str(token_identity())):
            return make_response( 
                'Sequence not found', 
                404
            ) 
        else:
            data = check_data(
                model, 
                request.data, 
                force_default={'status':sequence.status}, 
                force_if_missing={
                    'user_id':sequence.user_id,
                    'challenge_id':sequence.challenge_id
                }
            )

            if 'error' in data:
                return make_response(data, 400)

            sequence.user_id = data['user_id']
            sequence.challenge_id = data['challenge_id']
            sequence.status = data['status']
            sequence.created_at = sequence.created_at
            sequence.updated_at = data['updated_at']
            if 'actions' in data:
                sequence.actions = data['actions']
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
                return make_response(jsonify({
                    'id': sequence.id,
                    'user_id': sequence.user_id, 
                    'challenge_id' : sequence.challenge_id, 
                    'status' : {
                        "code": sequence.status.name,
                        "label": sequence.status.value
                    },
                    "actions": sequence.actions,
                    "fb_seq_id": sequence.fb_seq_id,
                    "comments": sequence.comments,
                    'created_at': sequence.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': sequence.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                }), 200)

    @admin_required
    @jwt_needed
    def delete(self, id):
        """
        Supprimer une séquence
        ---
        tags: 
            - Séquences
        parameters:
            - in: path
              name: id
              required: true
              description: sequence id
        responses:
            200:
                description: sequence deleted
            404:
                description: sequence id not found
        """
        sequence = model.query.get(id)
        if not sequence: 
            return make_response( 
                'Sequence not found', 
                404
            )
        else:
            fb_seq_id = sequence.fb_seq_id
            db.session.delete(sequence)
            try:
                db.session.commit()
            except:
                return make_response( 
                    'Unable to delete sequence', 
                    400
                )
            else:
                if fb_seq_id:
                    # connect to farmbot api
                    fbot_token = None
                    try:
                        fbot_token = get_fbot_token()
                        if 'token' not in fbot_token.json:
                            return fbot_token
                    except Exception as e:
                        return make_response(jsonify({
                            "message": e
                        }), 400)

                    delete_sequence(fbot_token.json['token'], fb_seq_id)

                return make_response( 
                    'Sequence deleted', 
                    200
                )

def UpdateStatus(id, status, data, **kwargs):
    sequence = model.query.get(id)
    
    if (not sequence) or (str(token_role()) != 'Administrateur' and str(sequence.user_id) != str(token_identity())):
        return make_response( 
            'Sequence not found', 
            404
        ) 
    else:
        data = check_data(
            model, 
            request.data, 
            force_if_missing={
                'user_id':sequence.user_id,
                'challenge_id':sequence.challenge_id,
                'status':status
            }
        )
        sequence.status = status
        if kwargs.get('seq_id'):
            sequence.fb_seq_id = kwargs.get('seq_id')
        if 'actions' in data:
            sequence.actions = data['actions']
        sequence.created_at = sequence.created_at
        sequence.updated_at = data['updated_at']

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
            return make_response(jsonify({
                'id': sequence.id,
                'user_id': sequence.user_id, 
                'challenge_id' : sequence.challenge_id, 
                'status' : {
                    "code": sequence.status.name,
                    "label": sequence.status.value
                },
                "actions": sequence.actions,
                "fb_seq_id": sequence.fb_seq_id,
                "comments": sequence.comments,
                'created_at': sequence.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': sequence.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                "celery": kwargs.get('celery') if kwargs.get('celery') else None
            }), 200)

class Send_To_Wip(Resource):
    @jwt_needed
    def put(self, id):
        """
        Remettre une séquence en statut En cours
        ---
        tags: 
            - Séquences
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: sequence id
            - in: body
              name: body
              required: true
              schema:
                required:
                    - user_id
                    - challenge_id
                properties:
                    challenge_id:
                        type: string
                        format: uuid
                        description: Linked challenge (id)
                    user_id:
                        type: string
                        format: uuid
                        description: Creator of the sequence (user id)
                    actions:
                        type: array
                        description: List of actions
                        items:
                            type: object
                            properties:
                                position:
                                    type: integer
                                type:
                                    type: string
                                    enum: ['find_home', 'humidity', 'move_absolute', 'move_relative', 'take_photo', 'wait', 'water']
                                param:
                                    type: object
                    comments:
                        type: array
                        description: List of user cemments
                        items:
                            schema:
                                #ref": "#/definitions/sequence_comment
        responses:
            200:
                description: updated sequence
                schema:
                    type: object
                    $ref: '#/definitions/sequence'
            400:
                description: wrong query
            404:
                description: sequence id not found
        """
        return UpdateStatus(id, 'WIP', request.data)

class Send_To_Process(Resource):
    @jwt_needed
    def put(self, id):
        """
        Envoyer une séquence au professeur pour validation
        ---
        tags: 
            - Séquences
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: sequence id
            - in: body
              name: body
              required: true
              schema:
                required:
                    - user_id
                    - challenge_id
                properties:
                    challenge_id:
                        type: string
                        format: uuid
                        description: Linked challenge (id)
                    user_id:
                        type: string
                        format: uuid
                        description: Creator of the sequence (user id)
                    actions:
                        type: array
                        description: List of actions
                        items:
                            type: object
                            properties:
                                position:
                                    type: integer
                                type:
                                    type: string
                                    enum: ['find_home', 'humidity', 'move_absolute', 'move_relative', 'take_photo', 'wait', 'water']
                                param:
                                    type: object
                    comments:
                        type: array
                        description: List of user cemments
                        items:
                            schema:
                                #ref": "#/definitions/sequence_comment
        responses:
            200:
                description: updated sequence
                schema:
                    type: object
                    $ref: '#/definitions/sequence'
            400:
                description: wrong query
            404:
                description: sequence id not found
        """
        return UpdateStatus(id, 'TO_PROCESS', request.data)

class Send_To_Process_Wip(Resource):
    @jwt_needed
    def put(self, id):
        """
        Envoyer une séquence à valider au farmbot
        ---
        tags: 
            - Séquences
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: sequence id
            - in: body
              name: body
              required: true
              schema:
                required:
                    - user_id
                    - challenge_id
                properties:
                    challenge_id:
                        type: string
                        format: uuid
                        description: Linked challenge (id)
                    user_id:
                        type: string
                        format: uuid
                        description: Creator of the sequence (user id)
                    actions:
                        type: array
                        description: List of actions
                        items:
                            type: object
                            properties:
                                position:
                                    type: integer
                                type:
                                    type: string
                                    enum: ['find_home', 'humidity', 'move_absolute', 'move_relative', 'take_photo', 'wait', 'water']
                                param:
                                    type: object
                    comments:
                        type: array
                        description: List of user cemments
                        items:
                            schema:
                                #ref": "#/definitions/sequence_comment
        responses:
            200:
                description: updated sequence
                schema:
                    type: object
                    $ref: '#/definitions/sequence'
            400:
                description: wrong query
            404:
                description: sequence id not found
        """
        # connect to farmbot api
        fbot_token = get_fbot_token()
        if 'token' not in fbot_token.json:
            return fbot_token
        
        try:
            sequence = model.query.get(id)
        except SQLAlchemyError as e:
            return make_response(jsonify({
                "message": "unable to get sequence",
                "db error" : str(e)
            }), 400)
        
        data = check_data(
            model, 
            request.data, 
            force_if_missing={
                'user_id':sequence.user_id,
                'challenge_id':sequence.challenge_id,
                'status':'PROCESS_WIP'
            }
        )
        if 'actions' in data:
            sequence.actions = data['actions']

        celery_script = sequence_action_to_celery(sequence)
        if 'error' in celery_script:
            return make_response(jsonify(celery_script), 400)

        fb_seq_id = sequence.fb_seq_id

        fb_seq = create_or_update_sequence(fbot_token.json['token'], celery_script, fb_seq_id)
        if 'id' not in fb_seq:
            return make_response(jsonify({
                "message": "unable to send sequence to farmbot",
                "error": fb_seq
            }), 400)

        return UpdateStatus(id, 'PROCESS_WIP', request.data, celery=celery_script, seq_id=fb_seq['id'])

class Send_Processed(Resource):
    @jwt_needed
    def put(self, id):
        """
        Valider une séquence
        ---
        tags: 
            - Séquences
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: sequence id
            - in: body
              name: body
              required: true
              schema:
                required:
                    - user_id
                    - challenge_id
                properties:
                    challenge_id:
                        type: string
                        format: uuid
                        description: Linked challenge (id)
                    user_id:
                        type: string
                        format: uuid
                        description: Creator of the sequence (user id)
                    actions:
                        type: array
                        description: List of actions
                        items:
                            type: object
                            properties:
                                position:
                                    type: integer
                                type:
                                    type: string
                                    enum: ['find_home', 'humidity', 'move_absolute', 'move_relative', 'take_photo', 'wait', 'water']
                                param:
                                    type: object
                    comments:
                        type: array
                        description: List of user cemments
                        items:
                            schema:
                                #ref": "#/definitions/sequence_comment
        responses:
            200:
                description: updated sequence
                schema:
                    type: object
                    $ref: '#/definitions/sequence'
            400:
                description: wrong query
            404:
                description: sequence id not found
        """
        return UpdateStatus(id, 'PROCESSED', request.data)

class Comments(Resource):
    @jwt_needed
    def post(self, id):
        """
        Ajouter un commentaire à une séquence
        ---
        tags: 
            - Séquences
        parameters:
            - in: path
              name: id
              required: true
              type: string
              format: uuid
              description: sequence id
            - in: body
              name: body
              required: true
              schema:
                properties:
                    comment:
                        type: string
                        description: user comment to add
        responses:
            200:
                description: list all sequence comments
                schema:
                    type: array
                    #ref: '#/definitions/sequence_comment'
            400:
                description: wrong body content
            404:
                description: sequence id not found
        """
        try:
            sequence = model.query.get(id)
        except SQLAlchemyError as e:
            return make_response(jsonify({
                "message": "unable to get sequence",
                "db error" : str(e)
            }), 404)
        
        user_id = str(token_identity())
        user_pseudo = str(token_pseudo())

        data = json.loads(request.data)

        if 'comment' in data:
            comment = {
                'user': {
                    'id': user_id,
                    'pseudo': user_pseudo
                },
                'comment': data['comment']
            }
        else:
            return make_response(jsonify({
                "error": {
                    "message": "missing field comment"
                }
            }), 400)

        comments = list(sequence.comments) if sequence.comments else []
        comments.append(comment)

        sequence.comments = comments
        
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
            return make_response(jsonify(sequence.comments), 200)
