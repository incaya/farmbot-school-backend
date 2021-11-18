#!/usr/bin/python
#coding: utf-8

import json
import config
from conftest import get_fixtures

model = 'users'

test_data = {}
with open('test_data.json', 'r') as f:
    test_data = json.loads(f.read())

def test_user(client, api_standard_tests):

    print('\nPOST /login as admin return 200')
    r = client.post('/api/login', json = {"email":config.getConfigKey('db.admin_email'),"password":config.getConfigKey('db.admin_password')})
    assert r.status_code == 200
    assert 'access_token' in r.json
    admin_token = r.json['access_token']
    print('>> get access_token : '+admin_token)

    usergroups_fixtures = get_fixtures('usergroups')
    r = client.post('/api/usergroups', json = usergroups_fixtures['data'], headers={"Authorization": "Bearer "+admin_token})
    usergroup = r.json['id']
    print('\nCreate user group to test user with group id : ', usergroup)

    user_fixtures = get_fixtures(
        model,
        data_param = {
            "group_id": usergroup
        }
    )

    # specific user tests : signup and login
    print('\n**** SPECIFIC TESTS ****')
    print('\nPOST /signup as a user role return 201')
    r = client.post('/api/signup', json = user_fixtures['data'])
    assert r.status_code == 201
    id = r.json['id']
    print('>> get id : '+id)
    
    print('\nPOST /signup with same user information return 202')
    r = client.post('/api/signup', json = user_fixtures['data'])
    assert r.status_code == 202
    print(r.data)
    
    print('\nPOST /login as user return 200')
    r = client.post('/api/login', json = {"email": user_fixtures['data']['email'], "password": user_fixtures['data']['password']})
    assert r.status_code == 200
    assert 'access_token' in r.json
    user_token = r.json['access_token']
    print('>> get access_token : '+user_token)

    print('\nGET user group to control user presence')
    r = client.get('/api/usergroups/'+usergroup, headers={"Authorization": "Bearer "+admin_token})
    assert r.status_code == 200

    print('\nGET /users as user proile return 403')
    assert client.get('/api/users', headers={"Authorization": "Bearer "+user_token}).status_code == 403

    print('\nDELETE id with user token return 403')
    assert client.delete('/api/users/'+id, headers={"Authorization": "Bearer "+user_token}).status_code == 403

    print('\nDELETE id with admin token return 200')
    assert client.delete('/api/users/'+id, headers={"Authorization": "Bearer "+admin_token}).status_code == 200

    print('\nPOST /login missing email or password return 401')
    r = client.post('/api/login', json = {})
    assert r.status_code == 401
    print(r.data)
    print(r.headers['WWW-Authenticate'])

    print('\nPOST /login with unknown user return 401')
    r = client.post('/api/login', json = {"email": user_fixtures['data']['email'], "password": user_fixtures['data']['password']})
    assert r.status_code == 401
    print(r.data)
    print(r.headers['WWW-Authenticate'])

    print('\nPOST /login with wrong password user return 403')
    r = client.post('/api/login', json = {"email": config.getConfigKey('db.admin_email'), "password": 'wrong_password'})
    assert r.status_code == 403
    print(r.data)
    print(r.headers['WWW-Authenticate'])
    
    assert api_standard_tests(
        client = client, 
        model = model,
        data_param = {
            "group_id": usergroup
        }
    )

    print('\nDELETE user group with admin token return 200')
    assert client.delete('/api/usergroups/'+usergroup, headers={"Authorization": "Bearer "+admin_token}).status_code == 200
