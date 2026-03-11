import json
import os
from decimal import Decimal
from utils.guest_dao import GuestDAO

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
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Guest not found'})
            }
        
        if guest.confirmed_assistance:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Cannot update confirmed guest'})
            }
        
        updated_guest = dao.update_guest(subdomain, confirmation_code, body)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'guest': updated_guest}, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
