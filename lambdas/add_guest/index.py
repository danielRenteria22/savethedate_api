import json
import os
from utils.guest_dao import GuestBuilder, GuestDAO

table_name = os.environ['TABLE_NAME']

def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        body = json.loads(event['body'])
        
        # Validate required fields
        required = ['name', 'phone_code', 'phone_number', 'num_guests']
        missing = [f for f in required if f not in body]
        if missing:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Missing fields: {", ".join(missing)}'})
            }
        
        # Validate types and formats
        if not isinstance(body['name'], str) or not body['name'].strip():
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'name must be a non-empty string'})
            }
        
        if not isinstance(body['phone_code'], str) or not body['phone_code'].startswith('+'):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'phone_code must be a string starting with +'})
            }
        
        if not isinstance(body['phone_number'], str) or not body['phone_number'].strip():
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'phone_number must be a non-empty string'})
            }
        
        if not isinstance(body['num_guests'], int) or body['num_guests'] < 1:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'num_guests must be an integer >= 1'})
            }
        
        guest_data = GuestBuilder()\
            .event_id(subdomain)\
            .name(body['name'])\
            .phone_code(body['phone_code'])\
            .phone_number(body['phone_number'])\
            .num_guests(body['num_guests'])\
            .build()
        
        dao = GuestDAO(table_name)
        created_guest = dao.create_guest(guest_data)
        
        return {
            'statusCode': 201,
            'body': json.dumps({'guest': created_guest})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
