import json
import os
from utils.guest_dao import GuestDAO

table_name = os.environ['TABLE_NAME']

def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        confirmation_code = event['pathParameters']['guest_id']
        
        dao = GuestDAO(table_name)
        guest = dao.get_guest(subdomain, confirmation_code)
        
        if not guest:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Guest not found'})
            }
        
        dao.delete_guest(subdomain, confirmation_code)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Guest deleted successfully'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
