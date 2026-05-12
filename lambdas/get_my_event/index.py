import os
from utils.event_dao import EventDAO
from utils.response import cors_response

table_name = os.environ['TABLE_NAME']

def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        dao = EventDAO(table_name)
        my_event = dao.get_event(subdomain)

        if not my_event:
            return cors_response(404, {'error': 'Event not found'})

        return cors_response(200, {'event': my_event.__dict__})

    except Exception as e:
        return cors_response(500, {'error': str(e)})
