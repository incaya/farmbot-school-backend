import json
from resources.pin import getPinByAction
from resources.fbot_conf import get_fbot_token, getPin

def find_home(action):
    celery = {
        "kind": "find_home",
        "args": {
            "axis": action['param']['value'],
            "speed": 100
        }
    }

    return celery

def move(move_type, action):
    moves = {}
    if move_type == 'abs':
        move_type = 'axis_overwrite'
        if 'x_value' in action['param']:
            moves['x'] = action['param']['x_value']
        else:
            moves['x'] = 0
        if 'y_value' in action['param']:
            moves['y'] = action['param']['y_value']
        else:
            moves['y'] = 0
        if 'z_value' in action['param']:
            moves['z'] = action['param']['z_value']
        else:
            moves['z'] = 0

    if move_type == 'rel':
        move_type = 'axis_addition'
    
    if 'x_offset' in action['param']:
        moves['x_offset'] = action['param']['x_offset']
    if 'y_offset' in action['param']:
        moves['y_offset'] = action['param']['y_offset']
    if 'z_offset' in action['param']:
        moves['z_offset'] = action['param']['z_offset']

    if 'x_variance' in action['param']:
        moves['x_variance'] = action['param']['x_variance']
    if 'y_variance' in action['param']:
        moves['y_variance'] = action['param']['y_variance']
    if 'z_variance' in action['param']:
        moves['z_variance'] = action['param']['z_variance']

    if 'x_speed' in action['param']:
        moves['x_speed'] = action['param']['x_speed']
    if 'y_speed' in action['param']:
        moves['y_speed'] = action['param']['y_speed']
    if 'z_speed' in action['param']:
        moves['z_speed'] = action['param']['z_speed']

    celery = {
        "kind": "move",
        "args": {},
        "body": []
    }

    for a in ['','_offset','_variance','_speed']:
        for axis in ['x','y','z']:
            field = axis+a
            operand = 'random' if a == '_variance' else 'numeric'
            axis_arg = 'speed_setting' if a == '_speed' else 'axis_operand'
            args_field = 'variance' if a == '_variance' else 'number'
            kind = move_type
            if a == '_offset':
                kind = 'axis_addition'
            if a == '_variance':
                kind = 'axis_addition'
            if a == '_speed':
                kind = 'speed_overwrite'
            if field in moves:
                celery['body'].append(
                    {
                        "kind": kind,
                        "args": {
                            "axis": axis,
                            axis_arg: {
                                "kind": operand,
                                "args": {
                                    args_field: int(moves[field])
                                }
                            }
                        }
                    }
                )

    return celery

def take_photo():
    celery = {
        "kind": "take_photo",
        "args": {}
    }

    return celery

def pin(pin_action_type, pin_action, action):
    pin = getPinByAction(pin_action)

    if not pin:
        return {
            "error": 'no_'+str(pin_action)+'_action_pin',
            "message": 'Please verify you correctly configure action '+str(pin_action)
        }

    # connect to farmbot api
    fbot_token = get_fbot_token()
    if 'token' not in fbot_token.json:
        return fbot_token
    
    fb_pin = getPin(fbot_token.json['token'], pin.material_type.value, pin.material_id)
    
    if not fb_pin:
        return {
            "error": 'no_'+str(pin_action)+'_pin_on_farmbot',
            "message": 'Please verify you correctly configure on farmbot pin with number '+str(pin.material_id)
        }

    if 'error' in fb_pin:
        return fb_pin

    if pin_action_type == 'write_pin':
        return {
            "kind": pin_action_type,
            "args": {
                "pin_number": {
                    "kind": "named_pin",
                    "args": {
                        "pin_type": pin.material_type.value,
                        "pin_id": fb_pin['id']
                    }
                },
                "pin_value": int(action['param']['value']),
                "pin_mode": fb_pin['mode']
            }
        }
    else:
        return {
            "kind": pin_action_type,
            "args": {
                "pin_number": {
                    "kind": "named_pin",
                    "args": {
                        "pin_type": pin.material_type.value,
                        "pin_id": fb_pin['id']
                    }
                },
                "pin_mode": fb_pin['mode'],
                "label": fb_pin['label']
            }
        }

def sequence_action_to_celery(sequence):
    actions = sequence.actions
    celery = []
    for action in actions:
        if action['type'] == 'find_home':
            celery.append(find_home(action))
        if action['type'] == 'move_absolute':
            celery.append(move('abs', action))
        if action['type'] == 'move_relative':
            celery.append(move('rel', action))
        if action['type'] == 'take_photo':
            celery.append(take_photo())
        if action['type'] == 'water':
            if 'param' not in action:
                return {
                    'error': 'param not in water action'
                }
            if 'type' not in action['param']:
                return {
                    'error': 'type not in water action param'
                }
            water = pin(str(action['param']['type'])+'_pin', 'water', action)
            if 'error' in water:
                return water
            else:
                celery.append(water)
        if action['type'] == 'vacuum':
            if 'param' not in action:
                return {
                    'error': 'param not in vacuum action'
                }
            if 'type' not in action['param']:
                return {
                    'error': 'type not in vacuum action param'
                }
            vacuum = pin(str(action['param']['type'])+'_pin', 'vacuum', action)
            if 'error' in vacuum:
                return vacuum
            else:
                celery.append(vacuum)
        if action['type'] == 'humidity':
            if 'param' not in action:
                return {
                    'error': 'param not in humidity action'
                }
            if 'type' not in action['param']:
                return {
                    'error': 'type not in humidity action param'
                }
            humidity = pin(str(action['param']['type'])+'_pin', 'humidity', action)
            if 'error' in humidity:
                return humidity
            else:
                celery.append(humidity)
        if action['type'] == 'wait':
            celery.append(
                {
                    "kind": "wait",
                    "args": {
                        "milliseconds": int(action['param']['milliseconds'])
                    }
                }
            )
    return {
        'name': sequence.challenge.title  + ' / ' + sequence.user.pseudo,
        'kind': 'sequence',
        'body': celery
    }
