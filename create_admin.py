import config

from werkzeug.security import generate_password_hash

from db import conn
from db.models import User

db = conn.db

me = User(
    email=config.getConfigKey('db.admin_email'),
    password=generate_password_hash(config.getConfigKey('db.admin_password')),
    pseudo=config.getConfigKey('db.admin_pseudo'),
    role='ADMIN'
)
db.session.add(me)
db.session.commit()