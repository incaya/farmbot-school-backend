#!/usr/bin/python
#coding: utf-8

import config
from conftest import get_fixtures

model = 'challenges'

def test_challenge(client, api_standard_tests):

    print('\nPOST /login as admin return 200')
    r = client.post('/api/login', json = {"email":config.getConfigKey('db.admin_email'),"password":config.getConfigKey('db.admin_password')})
    assert r.status_code == 200
    assert 'access_token' in r.json
    admin_token = r.json['access_token']
    print('>> get access_token : '+admin_token)

    usergroups_fixtures = get_fixtures('usergroups')
    usergroups_data = usergroups_fixtures['data']
    usergroups_data['generate_learners'] = 0
    r = client.post('/api/usergroups', json = usergroups_fixtures['data'], headers={"Authorization": "Bearer "+admin_token})
    usergroup = r.json['id']
    print('\nCreate user group to test user with group id : ', usergroup)

    assert api_standard_tests(
        client = client, 
        model = model,
        data_param = {
            "group_id": usergroup
        }
    )

    r = client.post('/api/signup', json = get_fixtures('users', data_param = {"group_id": usergroup})['data'])
    user = r.json['id']
    print('\nCreate user to test sequence with id : ', user)

    r = client.post('/api/login', json = {"email":"user_test@user.fr","password":"my_pass_to_test","group_id":usergroup})
    user_token = r.json['access_token']
    print('\nLog in with user : ', user_token)

    print('\nPOST test challenge return 200')
    r = client.post('/api/'+model, json = get_fixtures(model, data_param = {"group_id": usergroup})['data'], headers={"Authorization": "Bearer "+admin_token})
    assert r.status_code == 200
    challenge = r.json['id']
    print('>> get id : '+challenge)

    print('\nGet test challenge with user return 200')
    r = client.get('/api/'+model, headers={"Authorization": "Bearer "+user_token})
    assert r.status_code == 200
    
    print('\nDELETE test challenge with admin token return 200')
    client.delete('/api/'+model+'/'+challenge, headers={"Authorization": "Bearer "+admin_token})

    print('\nDELETE user with admin token return 200')
    client.delete('/api/users/'+user, headers={"Authorization": "Bearer "+admin_token})

    print('\nDELETE user group with admin token return 200')
    client.delete('/api/usergroups/'+usergroup, headers={"Authorization": "Bearer "+admin_token})
