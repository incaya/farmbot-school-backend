#!/usr/bin/env python

import json
import os
import os.path

CC_MATCH = {
    "farmbot-api.url": "FARMBOT_API_URL",
    "farmbot-api.email": "FARMBOT_API_EMAIL",
    "farmbot-api.password": "FARMBOT_API_PASSWORD",
    "db.host": "POSTGRESQL_ADDON_HOST",
    "db.port": "POSTGRESQL_ADDON_PORT",
    "db.name": "POSTGRESQL_ADDON_DB",
    "db.user": "POSTGRESQL_ADDON_USER",
    "db.password": "POSTGRESQL_ADDON_PASSWORD",
    "jwt.secret_key": "JWT_SECRET_KEY",
    "jwt.expiration_time": "JWT_EXPIRATION_TIME"
}

def getConfigKey(key):
    if os.getenv('CC_ENV'):
        return os.getenv(CC_MATCH[key])
    else:
        tree = key.split('.')
        keyValue = None
        project_root = os.path.dirname(__file__)
        with open(os.path.join(project_root, 'config.json'), 'r') as f:
            conf = f.read()
            keyValue = json.loads(conf)
            for k in tree:
                keyValue = keyValue[k]
        return keyValue
