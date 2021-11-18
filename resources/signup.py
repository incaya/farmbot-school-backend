#!/usr/bin/python
#coding: utf-8

import json
import config

from flask import request, jsonify, make_response 
from flask_restful import Resource

from sqlalchemy.exc import SQLAlchemyError

from werkzeug.security import generate_password_hash

from db import conn
from db.models import User, UserRoles

from utils.sanitizers import check_data

db = conn.db

class Signup(Resource):
    def post(self): 
        """
         
        ---
        tags: 
            - Créer un compte utilisateur
        parameters:
            - in: body
              name: body
              required: true
              schema:
                required:
                    - email
                    - password
                    - pseudo
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
        responses:
            201:
                description: user id
                schema:
                    properties:
                        message:
                            type: string
                            default: "Successfully registered"
                        id:
                            type: string
                            description: created user id
            202:
                description: user email or name already exists
            400:
                description: wrong body content
        """

        # creates a dictionary of the form data 
        data = check_data(User(), request.data)

        if 'error' in data:
            return make_response(data, 400)

        if 'password' not in data:
            return {"error": { "message": "error in request data", "missing_field": "password" }}

        data['role'] = UserRoles.USER
        data['password'] = generate_password_hash(data['password'])

        # checking for existing user 
        user = User.query\
            .filter_by(email = data['email'])\
            .first() 
        if not user: 
            # database ORM object 
            user = User(**data) 
            # insert user 
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
                    "message": "Successfully registered",
                    "id": user.id
                }), 201)
        else:
            # returns 202 if user already exists 
            return make_response('User already exists. Please Log in.', 202)