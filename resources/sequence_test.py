#!/usr/bin/python
#coding: utf-8

import config
import json
from conftest import get_fixtures

model = 'sequences'

def test_sequence(client, api_standard_tests):

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

    users_fixtures = get_fixtures('users',
        data_param = {
            "group_id": usergroup
        }
    )
    pins_fixtures = get_fixtures('pins')

    r = client.post('/api/signup', json = users_fixtures['data'])
    user = r.json['id']
    print('\nCreate user to test sequence with id : ', user)
    
    r = client.post('/api/login', json = {"email":"user_test@user.fr","password":"my_pass_to_test"})
    user_token = r.json['access_token']
    print('\nLog in with user to check user seq : ', user_token)

    challenges_fixtures = get_fixtures('challenges',
        data_param = {
            "group_id": usergroup
        }
    )

    r = client.post('/api/challenges', json = challenges_fixtures['data'], headers={"Authorization": "Bearer "+admin_token})
    challenge = r.json['id']
    print('\nCreate challenge to test sequence with id : ', challenge)

    assert api_standard_tests(
        client = client, 
        model = model,
        data_param = {
            "user_id": user,
            "challenge_id": challenge
        }
    )

    sequences_fixtures = get_fixtures(
        'sequences',
        data_param = {
            "user_id": user,
            "challenge_id": challenge
        }
    )

    r = client.post('/api/sequences', json = sequences_fixtures['data'], headers={"Authorization": "Bearer "+admin_token})
    sequence = r.json['id']
    print('\nCreate sequence to test status update ', sequence)
    
    print('\nSequence test status update to process')
    r = client.put(
        '/api/sequences/'+sequence+'/to_process', 
        json = sequences_fixtures['data'], 
        headers={"Authorization": "Bearer "+admin_token}
    )
    assert r.status_code == 200
    assert r.json['status']['code'] == 'TO_PROCESS'

    print('\nSequence test status update to send to farmbot without pin created')
    r = client.put(
        '/api/sequences/'+sequence+'/send_to_farmbot',
        json = sequences_fixtures['data'],
        headers={"Authorization": "Bearer "+admin_token}
    )
    assert r.status_code == 400
    assert r.json['error'] == 'no_water_action_pin'

    r = client.post('/api/pins', json = pins_fixtures['data'], headers={"Authorization": "Bearer "+admin_token})
    pin = r.json['id']
    print('\nCreate pin to test sequence with id : ', pin)

    print('\nSequence test status update to send to farmbot')
    r = client.put(
        '/api/sequences/'+sequence+'/send_to_farmbot', 
        json = sequences_fixtures['data'],
        headers={"Authorization": "Bearer "+admin_token}
    )
    assert r.status_code == 200
    assert r.json['status']['code'] == 'PROCESS_WIP'
    assert r.json['celery'] != None
    assert r.json['fb_seq_id'] != None

    print('\nSequence test status update data send to farmbot')
    r = client.put(
        '/api/sequences/'+sequence+'/send_to_farmbot', 
        json = sequences_fixtures['update_send_to_farmbot'],
        headers={"Authorization": "Bearer "+admin_token}
    )
    assert r.status_code == 200
    assert r.json['status']['code'] == 'PROCESS_WIP'
    assert r.json['celery'] != None
    assert r.json['fb_seq_id'] != None

    print('\nSequence test status update to processed')
    r = client.put(
        '/api/sequences/'+sequence+'/processed', 
        json = sequences_fixtures['data'],
        headers={"Authorization": "Bearer "+admin_token}
    )
    assert r.status_code == 200
    assert r.json['status']['code'] == 'PROCESSED'

    print('\nSequence test status update to wip')
    r = client.put(
        '/api/sequences/'+sequence+'/to_wip',
        json = sequences_fixtures['data'],
        headers={"Authorization": "Bearer "+admin_token}
    )
    assert r.status_code == 200
    assert r.json['status']['code'] == 'WIP'

    print('\nCheck user sequence id in challenge')
    r = client.get('/api/challenges/'+challenge, headers={"Authorization": "Bearer "+user_token})
    assert r.status_code == 200
    assert r.json['user_seq'] == sequence

    print('\nCheck user sequence id in challenges list')
    r = client.get('/api/challenges', headers={"Authorization": "Bearer "+user_token})
    assert r.status_code == 200
    for c in r.json['challenges']:
        if str(c['id']) == str(challenge):
            assert c['user_seq'] == sequence

    r = client.post('/api/sequences/'+sequence+'/comments', json = { 'comment': 'my first test comment'}, headers={"Authorization": "Bearer "+user_token})
    print('\nAdd first comment to sequence ', sequence)
    assert r.status_code == 200

    r = client.post('/api/sequences/'+sequence+'/comments', json = { 'comment': 'my second test comment'}, headers={"Authorization": "Bearer "+admin_token})
    print('\nAdd second comment to sequence ', sequence)
    assert r.status_code == 200

    client.delete('/api/sequences/'+sequence, headers={"Authorization": "Bearer "+admin_token})
    
    r = client.post('/api/sequences', json = sequences_fixtures['data'], headers={"Authorization": "Bearer "+user_token})
    sequence = r.json['id']
    print('\nCreate sequence with user force ', sequence)
    assert r.status_code == 200
    assert str(r.json['user_id']) == str(user)

    client.delete('/api/sequences/'+sequence, headers={"Authorization": "Bearer "+admin_token})
    client.delete('/api/challenges/'+challenge, headers={"Authorization": "Bearer "+admin_token})
    client.delete('/api/pins/'+pin, headers={"Authorization": "Bearer "+admin_token})
    client.delete('/api/users/'+user, headers={"Authorization": "Bearer "+admin_token})
    client.delete('/api/usergroups/'+usergroup, headers={"Authorization": "Bearer "+admin_token})
