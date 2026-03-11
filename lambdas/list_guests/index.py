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
        
        dao = GuestDAO(table_name)
        guests = dao.get_guests_by_event(subdomain)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'guests': [g.__dict__ for g in guests]}, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
