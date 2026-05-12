import json
import os
from utils.guest_dao import GuestBuilder, GuestDAO
from utils.response import cors_response

table_name = os.environ['TABLE_NAME']

def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        body = json.loads(event['body'])
        
        required = ['name', 'phone_code', 'phone_number', 'num_guests']
        missing = [f for f in required if f not in body]
        if missing:
            return cors_response(400, {'error': f'Missing fields: {", ".join(missing)}'})
        
        if not isinstance(body['name'], str) or not body['name'].strip():
            return cors_response(400, {'error': 'name must be a non-empty string'})
        
        if not isinstance(body['phone_code'], str) or not body['phone_code'].startswith('+'):
            return cors_response(400, {'error': 'phone_code must be a string starting with +'})
        
        if not isinstance(body['phone_number'], str) or not body['phone_number'].strip():
            return cors_response(400, {'error': 'phone_number must be a non-empty string'})
        
        if not isinstance(body['num_guests'], int) or body['num_guests'] < 1:
            return cors_response(400, {'error': 'num_guests must be an integer >= 1'})
        
        builder = GuestBuilder()\
            .event_id(subdomain)\
            .name(body['name'])\
            .phone_code(body['phone_code'])\
            .phone_number(body['phone_number'])\
            .num_guests(body['num_guests'])
        
        if 'civil_wedding_invitation' in body:
            builder = builder.civil_wedding_invitation(bool(body['civil_wedding_invitation']))
        if 'after_party_invitation' in body:
            builder = builder.after_party_invitation(bool(body['after_party_invitation']))
        if 'table' in body:
            builder = builder.table(body['table'])
        
        guest_data = builder.build()
        
        dao = GuestDAO(table_name)
        created_guest = dao.create_guest(guest_data)
        
        return cors_response(201, {'guest': created_guest})
        
    except Exception as e:
        return cors_response(500, {'error': str(e)})
