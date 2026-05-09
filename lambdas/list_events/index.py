import os
from utils.event_dao import EventDAO
from utils.response import cors_response

table_name = os.environ['TABLE_NAME']

def handler(event, context):
    try:
        groups = event['requestContext']['authorizer'].get('groups', '')
        if 'admin' not in groups:
            return cors_response(403, {'error': 'Forbidden: Admin access required'})
        
        dao = EventDAO(table_name)
        events = dao.list_events()
        return cors_response(200, {'events': events})
        
    except Exception as e:
        return cors_response(500, {'error': str(e)})
