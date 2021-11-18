#!/usr/bin/python
#coding: utf-8

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

import config

db_param = {
    "host": config.getConfigKey('db.host'),
    "port": config.getConfigKey('db.port'),
    "name": config.getConfigKey('db.name'),
    "user": config.getConfigKey('db.user'),
    "password": config.getConfigKey('db.password')
}

class conn():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://'+db_param['user']+':'+db_param['password']+'@'+db_param['host']+':'+db_param['port']+'/'+db_param['name']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db = SQLAlchemy(app)
    migrate = Migrate(app, db)
