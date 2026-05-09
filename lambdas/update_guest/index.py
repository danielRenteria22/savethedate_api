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
        confirmation_code = event['pathParameters']['guest_id']
        body = json.loads(event['body'])
        
        dao = GuestDAO(table_name)
        guest = dao.get_guest(subdomain, confirmation_code)
        
        if not guest:
            return cors_response(404, {'error': 'Guest not found'})
        
        if guest.confirmed_assistance:
            return cors_response(400, {'error': 'Cannot update confirmed guest'})
        
        updated_guest = dao.update_guest(subdomain, confirmation_code, body)
        
        response = cors_response(200, {'guest': updated_guest})
        response['body'] = json.dumps({'guest': updated_guest}, default=decimal_default)
        return response
        
    except Exception as e:
        return cors_response(500, {'error': str(e)})
