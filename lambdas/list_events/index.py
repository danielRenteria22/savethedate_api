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
        groups = event['requestContext']['authorizer'].get('groups', '')
        if 'admin' not in groups:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden: Admin access required'})
            }
        
        dao = EventDAO(table_name)
        events = dao.list_events()
        
        return {
            'statusCode': 200,
            'body': json.dumps({'events': events}, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
