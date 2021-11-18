#!/usr/bin/python
#coding: utf-8

import config
from conftest import get_fixtures

model = 'usergroups'

def test_usergroup(client, api_standard_tests):

    assert api_standard_tests(
        client = client, 
        model = model
    )

    print('\nPOST /login as admin return 200')
    r = client.post('/api/login', json = {"email":config.getConfigKey('db.admin_email'),"password":config.getConfigKey('db.admin_password')})
    assert r.status_code == 200
    assert 'access_token' in r.json
    admin_token = r.json['access_token']
    print('>> get access_token : '+admin_token)

    usergroup_fixtures = get_fixtures(model)
    usergroup_fixtures['data']['generate_learners'] = 0

    print('\nCreate usergroup')
    r = client.post('/api/usergroups', json = usergroup_fixtures['data'], headers={"Authorization": "Bearer "+admin_token})
    assert r.status_code == 200
    usergroup = r.json['id']

    user_fixtures = get_fixtures(
        'users',
        data_param = {
            "group_id": usergroup
        }
    )
    print('\nCreate user for usergroup')
    r = client.post('/api/users', json = user_fixtures['data'], headers={"Authorization": "Bearer "+admin_token})
    assert r.status_code == 200
    user = r.json['id']

    challenge_fixtures = get_fixtures(
        'challenges',
        data_param = {
            "group_id": usergroup
        }
    )
    print('\nCreate challenge for usergroup')
    r = client.post('/api/challenges', json = challenge_fixtures['data'], headers={"Authorization": "Bearer "+admin_token})
    assert r.status_code == 200
    challenge = r.json['id']

    print('\nGet usergroup')
    r = client.get('/api/usergroups/'+usergroup, headers={"Authorization": "Bearer "+admin_token})
    assert r.status_code == 200
    d = r.json
    assert len(d['users']) == 1
    assert len(d['challenges']) == 1

    print('\nDelete challenge')
    assert client.delete('/api/challenges/'+challenge, headers={"Authorization": "Bearer "+admin_token}).status_code == 200

    print('\nDelete user')
    assert client.delete('/api/users/'+user, headers={"Authorization": "Bearer "+admin_token}).status_code == 200

    print('\nDelete usergroup')
    assert client.delete('/api/usergroups/'+usergroup, headers={"Authorization": "Bearer "+admin_token}).status_code == 200
