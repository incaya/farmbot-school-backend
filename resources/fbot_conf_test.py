#!/usr/bin/python
#coding: utf-8

import config

data = {
    "url": config.getConfigKey('farmbot-api.url'),
    "email": config.getConfigKey('farmbot-api.email'),
    "password": config.getConfigKey('farmbot-api.password')
}

missing_field_data = {
    "url": config.getConfigKey('farmbot-api.url'),
    "email": config.getConfigKey('farmbot-api.email')
}

wrong_format_data = {
    "url": config.getConfigKey('farmbot-api.url'),
    "email": config.getConfigKey('farmbot-api.email'),
    "password": ""
}

def test_farmbot_config(client):
    print('\nPOST /login as admin return 200')
    r = client.post('/api/login', json = {"email":config.getConfigKey('db.admin_email'),"password":config.getConfigKey('db.admin_password')})
    assert r.status_code == 200
    assert 'access_token' in r.json
    admin_token = r.json['access_token']
    print('>> get access_token : '+admin_token)

    print('\nPOST /get_fbot_token as a admin role and good connexion info return 200')
    r = client.post('/api/get_fbot_token',  headers={"Authorization": "Bearer "+admin_token}, json = data)
    assert r.status_code == 200
    fbot_token = r.json['token']
    print('>> get farmbot token : '+fbot_token)

    # print('\nPOST /get_fbot_token as a admin role and missing fields return 400')
    # r = client.post('/api/get_fbot_token',  headers={"Authorization": "Bearer "+admin_token}, json = missing_field_data)
    # # assert r.json['message'] == 'unable to get farmbot api token'
    # assert r.status_code == 400

    # print('\nPOST /get_fbot_token as a admin role and bad connexion info return 400')
    # r = client.post('/api/get_fbot_token',  headers={"Authorization": "Bearer "+admin_token}, json = wrong_format_data)
    # assert r.json['message'] == 'unable to get farmbot api token'
    # assert r.status_code == 400
