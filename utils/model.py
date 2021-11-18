import datetime

def is_mandatory(field_list, field):
    for k,v in field_list.items():
        if k == field and 'mandatory' in v and v['mandatory']:
            return True
    return False

def mandatory_fields(field_list):
    f = []
    for k in field_list:
        if is_mandatory(field_list, k):
            f.append(k)
    return f

def not_is_allow_empty(field_list, field):
    for k,v in field_list.items():
        if k == field and 'allow_empty' in v and v['allow_empty']:
            return False
    return True

def not_allow_empty_fields(field_list):
    f = []
    for k in field_list:
        if not_is_allow_empty(field_list, k):
            f.append(k)
    return f

def as_dict(obj, **kwargs):
    special_fields = kwargs.get('special_fields')
    fields = [f.name for f in obj.__table__.columns]
    loaded_fields = [f for f in fields if f not in kwargs.get('unloaded_fields')] if kwargs.get('unloaded_fields') else fields
    result = {}
    for c in loaded_fields:
        if not special_fields or c not in special_fields:
            if c == 'created_at' or c == 'updated_at':
                result[c] = getattr(obj, c).strftime('%Y-%m-%d %H:%M:%S') if getattr(obj, c) else None
            else:
                result[c] = getattr(obj, c)
        elif special_fields[c] == 'enum':
            result[c] = {
                'code': getattr(obj, c).name if getattr(obj, c) else None,
                'label': getattr(obj, c).value if getattr(obj, c) else None
            }
        elif special_fields[c] == 'date':
            result[c] = getattr(obj, c).strftime('%Y-%m-%d') if getattr(obj, c) else None
        elif special_fields[c] == 'datetime':
            result[c] = getattr(obj, c).strftime('%Y-%m-%d %H:%M:%S') if getattr(obj, c) else None
        else:
            result[c] = getattr(obj, c)
    return result
