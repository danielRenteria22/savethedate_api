import json
import os
import boto3
from botocore.exceptions import ClientError
from utils.event_dao import EventDAO

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
        
        dao = EventDAO(table_name)
        dao.delete_event(subdomain)
        
        # Delete Cognito user
        try:
            cognito.admin_delete_user(
                UserPoolId=user_pool_id,
                Username=subdomain
            )
        except ClientError:
            pass  # User might not exist
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Event and user deleted successfully'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
