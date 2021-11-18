#!/usr/bin/python
#coding: utf-8

# Farmbot School Backend
# Copyright (C) 2021  INCAYA

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import config

from flask import Flask, Response, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flasgger import Swagger

from utils.jwt import JWT

from resources.fbot_conf import FarmbotConfig
from resources.pin import (Pins, Pin)
from resources.usergroup import (UserGroups, UserGroup)
from resources.user import (Users, User)
from resources.signup import Signup
from resources.login import Login
from resources.challenge import (Challenges, Challenge)
from resources.sequence import (Sequences, Sequence, Send_To_Wip, Send_To_Process, Send_To_Process_Wip, Send_Processed, Comments)

from db import conn

app = conn.app

JWT(app)
CORS(app)

template = {
  "swagger": "2.0",
  "info": {
    "title": "Farmbot School API",
    "description": "API for farmbot's extended features in education",
    "version": "0.1.0",
    "contact": {
      "name": "git repo",
      "url": "https://github.com/incaya/farmbot-school-api",
    }
  },
  "x-tagGroups": [
      {
        "name": "Connexion",
        "tags": ["Créer un compte utilisateur", "Se connecter à l'application"]
      },
      {
        "name": "Administration",
        "tags": ["Gestion des comptes", "Paramétrage", "Défis"]
      },
      {
        "name": "Fonctionnalités apprenants",
        "tags": ["Séquences"]
      }
  ],
  "definitions": {
    "pin": {
      "properties": {
        "id": {
          "type": "string",
          "format": "uuid",
          "description": "Pin id"
        },
        "material_type": {
          "type": "string",
          "description": "Material type",
          "enum": ['PERIPHERAL', 'SENSOR']
        },
        "material_id": {
            "type": "integer",
            "description": "Pin number"
        },
        "action": {
            "type": "string",
            "description": "Action related to pin"
        }
      }
    },
    "usergroup": {
      "properties": {
        "id": {
          "type": "string",
          "format": "uuid",
          "description": "UserGroup id"
        },
        "name": {
          "type": "string",
          "description": "UserGroup name"
        },
        "users": {
          "type": "array",
          "description": "UserGroup's users list",
          "items": {
            "type": "object",
            "schema": {
              "$ref": "#/definitions/user"
            }
          }
        },
        "challenges": {
          "type": "array",
          "description": "UserGroup's challenges list",
          "items": {
            "type": "object",
            "schema": {
              "$ref": "#/definitions/challenge"
            }
          }
        }
      }
    },
    "user": {
      "properties": {
        "id": {
          "type": "string",
          "format": "uuid",
          "description": "User id"
        },
        "pseudo": {
          "type": "string",
          "description": "User pseudo"
        },
        "name": {
          "type": "string",
          "description": "User name"
        },
        "email": {
          "type": "string",
          "format": "email",
          "description": "Email account"
        },
        "role": {
          "type": "string",
          "description": "user role",
          "enum": ['Administrateur', 'Utilisateur']
        },
        "sequences": {
          "type": "array",
          "description": "User's sequences list",
          "items": {
            "type": "object",
            "schema": {
              "$ref": "#/definitions/sequence"
            }
          }
        }
      }
    },
    "challenge": {
      "properties": {
        "id": {
          "type": "string",
          "format": "uuid",
          "description": "Challenge id"
        },
        "title": {
          "type": "string",
          "description": "Challenge title"
        },
        "end_date": {
          "type": "string",
          "format": "date",
          "description": "Challenge end date"
        },
        "description": {
          "type": "string",
          "description": "Challenge description"
        },
        "active": {
          "type": "boolean",
          "description": "Challenge activation flag"
        },
        "group_id": {
          "type": "string",
          "format": "uuid",
          "description": "User Group id"
        },
        "sequences": {
          "type": "array",
          "description": "Challenge's sequences list",
          "items": {
            "type": "object",
            "schema": {
              "$ref": "#/definitions/sequence"
            }
          }
        }
      }
    },
    "sequence": {
      "properties": {
        "id": {
          "type": "string",
          "format": "uuid",
          "description": "Sequence id"
        },
        "challenge_id": {
          "type": "string",
          "format": "uuid",
          "description": "Linked challenge (id)"
        },
        "user_id": {
          "type": "string",
          "format": "uuid",
          "description": "Creator of the sequence (user id)"
        },
        "status": {
          "type": "string",
          "description": "Sequence status",
          "enum": ['WIP', 'TO_PROCESS', 'PROCESS_WIP', 'PROCESSED']
        },
        "actions": {
          "type": "array",
          "description": "List of actions",
          "items": {
            "type": "object",
            "properties": {
              "position": {
                "type": "integer"
              },
              "type": {
                "type": "string",
                "enum": ['find_home', 'humidity', 'move_absolute', 'move_relative', 'take_photo', 'wait', 'water']
              },
              "param": {
                "type": "object"
              }
            }
          }
        },
        "fb_seq_id": {
          "type": "string",
          "format": "integer",
          "description": "Sequence id in farmbot app"
        },
        "comments": {
          "type": "array",
          "description": "List of user cemments",
          "items": {
            "schema": {
              "#ref": "#/definitions/sequence_comment"
            }
          }
        }
      }
    },
    "sequence_comment": {
      "properties": {
        "user": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "format": "uuid",
              "description": "User id"
            },
            "pseudo": {
              "type": "string",
              "description": "User pseudo"
            }
          }
        },
        "comment": {
          "type": "string",
          "description": "User comment"
        }
      }      
    }
  },
  "securityDefinitions": {
    "Bearer": {
      "type": "apiKey",
      "name": "Authorization",
      "in": "header",
      "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
    }
  },
  "security": [
    {
      "Bearer": [ ]
    }
  ]
}

Swagger(app, template=template)

@app.route('/')
def homepage():
   return redirect(url_for('flasgger.apidocs'))

api = Api(app)
api.add_resource(FarmbotConfig, '/api/get_fbot_token')
api.add_resource(Pins, '/api/pins')
api.add_resource(Pin, '/api/pins/<id>')
api.add_resource(Signup, '/api/signup')
api.add_resource(Login, '/api/login')
api.add_resource(UserGroups, '/api/usergroups')
api.add_resource(UserGroup, '/api/usergroups/<id>')
api.add_resource(Users, '/api/users')
api.add_resource(User, '/api/users/<id>')
api.add_resource(Challenges, '/api/challenges')
api.add_resource(Challenge, '/api/challenges/<id>')
api.add_resource(Sequences, '/api/sequences')
api.add_resource(Sequence, '/api/sequences/<id>')
api.add_resource(Send_To_Wip, '/api/sequences/<id>/to_wip')
api.add_resource(Send_To_Process, '/api/sequences/<id>/to_process')
api.add_resource(Send_To_Process_Wip, '/api/sequences/<id>/send_to_farmbot')
api.add_resource(Send_Processed, '/api/sequences/<id>/processed')
api.add_resource(Comments, '/api/sequences/<id>/comments')

if __name__ == '__main__':
    app.run(debug=True)
