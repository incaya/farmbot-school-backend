import json
import config

from functools import wraps

from flask import jsonify, request
from flask_jwt_extended import (JWTManager, verify_jwt_in_request, get_jwt_claims, get_jwt_identity)

def admin_required(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except:
            return {'error': 'access token error'}, 401
        claims = get_jwt_claims()
        if claims['role'] != 'Administrateur':
            return {'error': 'Admins only!'}, 403
        else:
            return fn(*args, **kwargs)
    return decorator

def jwt_needed(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except:
            return {'error': 'access token error'}, 401
        return fn(*args, **kwargs)
    return decorator

def token_identity():
    return get_jwt_identity()

def token_pseudo():
    claims = get_jwt_claims()
    return claims['pseudo']

def token_role():
    claims = get_jwt_claims()
    return claims['role']

def token_group():
    claims = get_jwt_claims()
    return claims['group']

class JWT(object):

    def __init__(self, app=None, **kwargs):
        self._options = kwargs
        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(self, app, **kwargs):
        app.config['JWT_SECRET_KEY'] = config.getConfigKey('jwt.secret_key')
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(config.getConfigKey('jwt.expiration_time'))

        jwt = JWTManager(app)

        @jwt.user_claims_loader
        def add_claims_to_access_token(user):
            return {
                "role": user.role.value,
                "pseudo": user.pseudo,
                "name": user.name,
                "group": user.group_id
            }

        @jwt.user_identity_loader
        def user_identity_lookup(user):
            return user.id

        return app