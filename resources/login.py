#!/usr/bin/python
#coding: utf-8

import json
import config

from flask import request, jsonify, make_response 
from flask_restful import Resource
from flask_jwt_extended import create_access_token

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime, timedelta 

from db.models import User

class Login(Resource):
    def post(self):
        """
         
        ---
        tags: 
            - Se connecter à l'application
        parameters:
            - in: body
              name: body
              required: true
              schema:
                required:
                    - email
                    - password
                properties:
                    email:
                        type: string
                        format: email
                        description: account email
                    password:
                        type: string
                        format: password
                        description: account password
        responses:
            200:
                description: connection token (JsonWebToken)
                schema:
                    properties:
                        access_token:
                            type: string
                            description: jwt token
            401:
                description: login required or user does not exist
            403:
                description: wrong password
        """

        # creates a dictionary of the form data 
        auth = json.loads(request.data) 
    
        if not auth or not auth['email'] or not auth['password']: 
            # returns 401 if any email or / and password is missing 
            return make_response( 
                'Could not verify', 
                401, 
                {'WWW-Authenticate' : 'Basic realm ="Login required !!"'} 
            ) 
    
        user = User.query\
            .filter_by(email = auth['email'])\
            .first() 

        if not user: 
            # returns 401 if user does not exist 
            return make_response( 
                'Could not verify', 
                401, 
                {'WWW-Authenticate' : 'Basic realm ="User does not exist !!"'} 
            )
    
        if check_password_hash(user.password, auth['password']): 
            # generates the JWT Token 
            access_token = create_access_token(identity=user)
            return make_response(jsonify(access_token=access_token), 200)

        # returns 403 if password is wrong 
        return make_response( 
            'Could not verify', 
            403, 
            {'WWW-Authenticate' : 'Basic realm ="Wrong Password !!"'} 
        )