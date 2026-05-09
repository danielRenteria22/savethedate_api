import json
import os
import boto3
from botocore.exceptions import ClientError
from utils.event_dao import EventDAO
from utils.guest_dao import GuestDAO
from utils.response import cors_response

cognito = boto3.client('cognito-idp')
table_name = os.environ['TABLE_NAME']
user_pool_id = os.environ['USER_POOL_ID']

def handler(event, context):
    try:
        groups = event['requestContext']['authorizer'].get('groups', '')
        if 'admin' not in groups:
            return cors_response(403, {'error': 'Forbidden: Admin access required'})
        
        subdomain = event['pathParameters']['subdomain']
        
        event_dao = EventDAO(table_name)
        if not event_dao.get_event(subdomain):
            return cors_response(404, {'error': 'Event not found'})
        
        guest_dao = GuestDAO(table_name)
        guests = guest_dao.get_guests_by_event(subdomain)
        for guest in guests:
            guest_dao.delete_guest(subdomain, guest.confirmation_code)
        
        event_dao.delete_event(subdomain)
        
        try:
            cognito.admin_delete_user(
                UserPoolId=user_pool_id,
                Username=subdomain
            )
        except ClientError:
            pass
        
        return cors_response(200, {'message': 'Event and user deleted successfully'})
        
    except Exception as e:
        return cors_response(500, {'error': str(e)})
