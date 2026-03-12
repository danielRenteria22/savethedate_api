import json
import os
from decimal import Decimal
from utils.event_dao import EventDAO

table_name = os.environ['TABLE_NAME']

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError

def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        body = json.loads(event['body'])
        
        # Only allow updating message and food_options
        allowed_fields = {'message', 'food_options'}
        updates = {k: v for k, v in body.items() if k in allowed_fields}
        
        if not updates:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No valid fields to update'})
            }
        
        dao = EventDAO(table_name)
        updated_event = dao.update_event(subdomain, updates)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'event': updated_event}, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
