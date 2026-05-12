import json
import os
from utils.event_dao import EventDAO
from utils.response import cors_response

table_name = os.environ['TABLE_NAME']

def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        body = json.loads(event['body'])

        allowed_fields = {'message', 'food_options'}
        updates = {k: v for k, v in body.items() if k in allowed_fields}

        if not updates:
            return cors_response(400, {'error': 'No valid fields to update'})

        dao = EventDAO(table_name)
        updated_event = dao.update_event(subdomain, updates)

        return cors_response(200, {'event': updated_event})

    except Exception as e:
        return cors_response(500, {'error': str(e)})
