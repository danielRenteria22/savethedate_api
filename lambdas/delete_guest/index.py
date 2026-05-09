import json
import os
from utils.guest_dao import GuestDAO
from utils.response import cors_response

table_name = os.environ['TABLE_NAME']

def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        confirmation_code = event['pathParameters']['guest_id']
        
        dao = GuestDAO(table_name)
        guest = dao.get_guest(subdomain, confirmation_code)
        
        if not guest:
            return cors_response(404, {'error': 'Guest not found'})
        
        dao.delete_guest(subdomain, confirmation_code)
        
        return cors_response(200, {'message': 'Guest deleted successfully'})
        
    except Exception as e:
        return cors_response(500, {'error': str(e)})
