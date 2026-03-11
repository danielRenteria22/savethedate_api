import json
import os
import boto3
from botocore.exceptions import ClientError
from utils.event_dao import EventDAO
from utils.guest_dao import GuestDAO

cognito = boto3.client('cognito-idp')
table_name = os.environ['TABLE_NAME']
user_pool_id = os.environ['USER_POOL_ID']

def handler(event, context):
    try:
        groups = event['requestContext']['authorizer'].get('groups', '')
        if 'admin' not in groups:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden: Admin access required'})
            }
        
        subdomain = event['pathParameters']['subdomain']
        
        event_dao = EventDAO(table_name)
        if not event_dao.get_event(subdomain):
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Event not found'})
            }
        
        # Delete all guests for this event
        guest_dao = GuestDAO(table_name)
        guests = guest_dao.get_guests_by_event(subdomain)
        for guest in guests:
            guest_dao.delete_guest(subdomain, guest.confirmation_code)
        
        # Delete event
        event_dao.delete_event(subdomain)
        
        # Delete Cognito user
        try:
            cognito.admin_delete_user(
                UserPoolId=user_pool_id,
                Username=subdomain
            )
        except ClientError:
            pass
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Event and user deleted successfully'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
