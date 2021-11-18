from flask_restful import reqparse

def init_reqparser():
    parser = reqparse.RequestParser()
    parser.add_argument('offset', type=int, help='The number of items to skip before starting to collect the result set')
    parser.add_argument('limit', type=int, help='The numbers of items to return')
    parser.add_argument('sort', type=str, help='Sorting a field ascending (field) or descending (-field)')
    
    return parser

def query_apply_reqparser(model, query, args):
    sort_arg = args['sort']
    sort = model.id.asc()
    if sort_arg:
        sort = getattr(model, sort_arg.replace('-', ''))
        if sort_arg[:1] == '-':
            sort = sort.desc()
        else:
            sort = sort.asc()
        query = query.order_by(sort)

    offset = args['offset']
    limit = args['limit']
    if offset and limit:
        query = query.limit(limit).offset(offset*limit)
    elif limit:
        query = query.limit(limit)

    return query
