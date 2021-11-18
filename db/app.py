#!/usr/bin/python
#coding: utf-8

from db import conn
from db.models import User, UserRoles, Challenge, Sequence

app = conn.app