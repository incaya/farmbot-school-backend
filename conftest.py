#!/usr/bin/python
#coding: utf-8

import pytest
import config
import json
from app import app as testapp

@pytest.fixture
def app():
    return testapp

def check_response(response, **kwargs):
    status = kwargs.get('expected_status', None)
    error_key = kwargs.get('expected_error_key', None)

    json_response = {}
    try:
        json_response = json.loads(response)
    except:
        return False

    return response.status_code == status and 'error' in json_response and error_key in json_response['error']

def get_fixtures(model, **kwargs):
    with open('test_data.json', 'r') as f:
        test_data = json.loads(f.read())
  
    data_param = kwargs.get('data_param')
    test_data_model = None
    if model in test_data:
        test_data_model = test_data[model]

        for k in test_data_model:
            if data_param:
                for d in data_param:
                    if d in test_data_model[k]:
                        test_data_model[k][d] = data_param[d]

    return test_data_model

@pytest.fixture
def api_standard_tests():
    def _std(**kwargs):
        all_passed  = True

        client = kwargs.get('client', None)
        model = kwargs.get('model', None)
        data_param = kwargs.get('data_param', None)

        test_data_model = get_fixtures(model=model, data_param=data_param)

        if test_data_model:
            data = test_data_model['data'] if 'data' in test_data_model else None
            data_for_change = test_data_model['data_for_change'] if 'data_for_change' in test_data_model else None
            changed_field = test_data_model['changed_field'] if 'changed_field' in test_data_model else None
            missing_field_data = test_data_model['missing_field_data'] if 'missing_field_data' in test_data_model else None
            empty_field_data = test_data_model['empty_field_data'] if 'empty_field_data' in test_data_model else None
            wrong_format_data = test_data_model['wrong_format_data'] if 'wrong_format_data' in test_data_model else None
            wrong_id = test_data_model['wrong_id'] if 'wrong_id' in test_data_model else None
        else:
            return False

        # standard resource tests
        print('\n**** STANDARD TESTS / ', model, ' ****')

        # log as admin
        print('\nPOST /login as admin return 200')
        r = client.post('/api/login', json = {"email":config.getConfigKey('db.admin_email'),"password":config.getConfigKey('db.admin_password')})
        all_passed = True if r.status_code == 200 else False
        all_passed = True if 'access_token' in r.json else False
        token = r.json['access_token']
        print('>> get access_token : '+token)

        # create test resource
        print('\nPOST return 200')
        r = client.post('/api/'+model, json = data, headers={"Authorization": "Bearer "+token})
        all_passed = True if r.status_code == 200 else False
        id = r.json['id']
        print('>> get id : '+id)

        # no auth
        print('\nPOST with not auth return 401')
        all_passed = True if client.post('/api/'+model, json = data).status_code == 401 else False
        
        print('\nGET with no auth return 401')
        all_passed = True if client.get('/api/'+model).status_code == 401 else False
        
        print('\nGET <id> with no auth return 401')
        all_passed = True if client.get('/api/'+model+'/'+id).status_code == 401 else False

        print('\nPUT <id> with no auth return 401')
        all_passed = True if client.put('/api/'+model+'/'+id, json = data_for_change).status_code == 401 else False

        print('\nDELETE <id> with no auth return 401')
        all_passed = True if client.delete('/api/'+model+'/'+id).status_code == 401 else False

        # missing fields
        print('\nPOST with missing field return 400')
        all_passed = check_response(
            client.post('/api/'+model, json = missing_field_data, headers={"Authorization": "Bearer "+token}),
            expected_status=400,
            expected_error_key='missing_field'
        )

        print('\nPUT <id> with missing field return 400')
        all_passed = check_response(
            client.put('/api/'+model+'/'+id, json = missing_field_data, headers={"Authorization": "Bearer "+token}),
            expected_status=400,
            expected_error_key='missing_field'
        )

        # empty field
        if empty_field_data:
            for d in empty_field_data:
                print('\nPOST with empty field return 400')
                all_passed = check_response(
                    client.post('/api/'+model, json = d, headers={"Authorization": "Bearer "+token}),
                    expected_status=400,
                    expected_error_key='empty_not_allowed_fields'
                )

                print('\nPUT <id> with empty field return 400')
                all_passed = check_response(
                    client.put('/api/'+model+'/'+id, json = d, headers={"Authorization": "Bearer "+token}),
                    expected_status=400,
                    expected_error_key='empty_not_allowed_fields'
                )

        # wrong format
        for d in wrong_format_data:
            print('\nPOST with wrong format field return 400')
            all_passed = check_response(
                client.post('/api/'+model, json = d, headers={"Authorization": "Bearer "+token}),
                expected_status=400,
                expected_error_key='db_error'
            )
            
            print('\nPUT <id> with wrong format field return 400')
            all_passed = check_response(
                client.put('/api/'+model+'/'+id, json = d, headers={"Authorization": "Bearer "+token}),
                expected_status=400,
                expected_error_key='db_error'
            )

        print('\nGET <wrong id> return 404')
        all_passed = True if client.get('/api/'+model+'/'+wrong_id, headers={"Authorization": "Bearer "+token}).status_code == 404 else False

        print('\nPUT <wrong id> return 404')
        all_passed = True if client.put('/api/'+model+'/'+wrong_id, headers={"Authorization": "Bearer "+token}).status_code == 404 else False

        print('\nDELETE <wrong id> with admin token return 404')
        all_passed = True if client.delete('/api/'+model+'/'+wrong_id, headers={"Authorization": "Bearer "+token}).status_code == 404 else False

        print('\nGET with admin token return 200')
        all_passed = True if client.get('/api/'+model, headers={"Authorization": "Bearer "+token}).status_code == 200 else False

        print('\nGET <id> with admin token return 200')
        all_passed = True if client.get('/api/'+model+'/'+id, headers={"Authorization": "Bearer "+token}).status_code == 200 else False

        print('\nPUT <id> to change field return 200')
        r = client.put('/api/'+model+'/'+id, json = data_for_change, headers={"Authorization": "Bearer "+token})
        all_passed = True if r.status_code == 200 else False
        all_passed = True if r.json[changed_field[0]] == changed_field[1] else False
        print('>> ', r.data)

        print('\nDELETE <id> with admin token return 200')
        all_passed = True if client.delete('/api/'+model+'/'+id, headers={"Authorization": "Bearer "+token}).status_code == 200 else False

        print('\nGET deleted id with admin token return 404')
        all_passed = True if client.get('/api/'+model+'/'+id, headers={"Authorization": "Bearer "+token}).status_code == 404 else False

        print('\nPUT deleted id with admin token return 404')
        all_passed = True if client.put('/api/'+model+'/'+id, headers={"Authorization": "Bearer "+token}).status_code == 404 else False

        return all_passed

    return _std
