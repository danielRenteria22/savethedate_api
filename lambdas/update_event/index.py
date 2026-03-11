import json
import os
from utils.event_dao import EventDAO

table_name = os.environ['TABLE_NAME']

def handler(event, context):
    try:
        groups = event['requestContext']['authorizer'].get('groups', '')
        if 'admin' not in groups:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden: Admin access required'})
            }
        
        subdomain = event['pathParameters']['subdomain']
        body = json.loads(event['body'])
        
        dao = EventDAO(table_name)
        updated_event = dao.update_event(subdomain, body)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'event': updated_event})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
