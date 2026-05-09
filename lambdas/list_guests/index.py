import json
import os
from decimal import Decimal
from utils.guest_dao import GuestDAO
from utils.response import cors_response

table_name = os.environ['TABLE_NAME']

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError

def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        
        dao = GuestDAO(table_name)
        guests = dao.get_guests_by_event(subdomain)
        
        response = cors_response(200, {'guests': [g.__dict__ for g in guests]})
        response['body'] = json.dumps({'guests': [g.__dict__ for g in guests]}, default=decimal_default)
        return response
        
    except Exception as e:
        return cors_response(500, {'error': str(e)})
