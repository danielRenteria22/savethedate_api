import json
import os
from utils.event_dao import EventDAO
from utils.response import cors_response

table_name = os.environ['TABLE_NAME']

def handler(event, context):
    try:
        groups = event['requestContext']['authorizer'].get('groups', '')
        if 'admin' not in groups:
            return cors_response(403, {'error': 'Forbidden: Admin access required'})
        
        subdomain = event['pathParameters']['subdomain']
        body = json.loads(event['body'])
        
        dao = EventDAO(table_name)
        if not dao.get_event(subdomain):
            return cors_response(404, {'error': 'Event not found'})
        
        updated_event = dao.update_event(subdomain, body)
        
        return cors_response(200, {'event': updated_event})
        
    except Exception as e:
        return cors_response(500, {'error': str(e)})
