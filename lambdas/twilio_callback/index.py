import json
import os
from utils.guest_dao import GuestDAO

table_name = os.environ['TABLE_NAME']

def handler(event, context):
    try:
        params = event.get('queryStringParameters', {})
        event_id = params.get('event_id')
        confirmation_code = params.get('confirmation_code')
        
        body = event.get('body', '')
        if isinstance(body, str):
            from urllib.parse import parse_qs
            body_params = parse_qs(body)
            message_status = body_params.get('MessageStatus', [None])[0]
        else:
            message_status = None
        
        if not event_id or not confirmation_code or not message_status:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required parameters'})
            }
        
        dao = GuestDAO(table_name)
        
        if message_status in ['sent', 'delivered']:
            dao.update_guest(event_id, confirmation_code, {'invitation_sent': True})
        elif message_status in ['failed', 'undelivered']:
            dao.update_guest(event_id, confirmation_code, {'invitation_sent_fatal_error': True})
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Status updated'})
        }
        
    except Exception as e:
        print(f"Error in callback: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
