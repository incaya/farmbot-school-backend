import json
from time import strftime,gmtime

def is_json(data):
    try:
        json_object = json.loads(data)
    except ValueError as e:
        return False
    return True

def check_data(model, data, **kwargs):
    if not is_json(data):
        return {"error": {"message": "request body must be json object"}}

    data = json.loads(data)

    data = populate_changes_dt(data)

    fd = kwargs.get('force_default')
    if fd:
        for f in fd: data[f] = fd[f]

    fm = kwargs.get('force_if_missing')
    if fm:
        for f in fm: 
            if f not in data:
                data[f] = fm[f]

    if kwargs.get('enum'):
        enum_check = check_enum_fields(kwargs.get('enum'), data)
        if enum_check:
            return enum_check
   
    missing_fields = check_missing_fields(model.mandatory, data)
    if missing_fields:
        return missing_fields
   
    not_allow_empty_fields = check_empty_fields(model.not_allow_empty, data)
    if not_allow_empty_fields:
        return not_allow_empty_fields

    return data

def check_missing_fields(mandatory, data):
    missing_field = [(field) for field in mandatory if not field in data]
    
    if missing_field:
        return {"error": { "message": "error in request data", "missing_field": missing_field }}
    
    return None

def check_empty_fields(not_allow_empty, data):
    empty_error = [(field) for field in not_allow_empty if field in data and data[field]=='']
    if empty_error:
        return {"error": { "message": "error in request data", "empty_not_allowed_fields": empty_error }}

    return None

def check_enum_fields(fields, data):
    if fields:
        for f in range(0, len(fields), 2):
            values = []
            for e in fields[f+1]:
                values.append(e.name)
            if data[fields[f]] not in values:
                return {"error": { "message": "error in request data", "db error" : "enum value incorrect on " + fields[f] }}

    return None

def populate_changes_dt(data):
    data['created_at'] = strftime("%Y-%m-%d %H:%M:%S")
    data['updated_at'] = strftime("%Y-%m-%d %H:%M:%S")
    return data
