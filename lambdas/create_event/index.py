import json
import os
import sys
import boto3
from botocore.exceptions import ClientError

from utils.event_dao import EventBuilder, EventDAO

cognito = boto3.client('cognito-idp')
table_name = os.environ['TABLE_NAME']
user_pool_id = os.environ['USER_POOL_ID']

def handler(event, context):
    try:
        # Check if user is admin
        groups = event['requestContext']['authorizer'].get('groups', '')
        if 'admin' not in groups:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden: Admin access required'})
            }
        
        body = json.loads(event['body'])
        
        # Validate required fields
        required = ['subdomain', 'guests_name', 'datetime_utc', 'food_options', 'password']
        missing = [f for f in required if f not in body]
        if missing:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Missing fields: {", ".join(missing)}'})
            }
        
        subdomain = body['subdomain']
        password = body['password']
        
        # Create event
        event_data = EventBuilder()\
            .subdomain(subdomain)\
            .guests_name(body['guests_name'])\
            .datetime_utc(body['datetime_utc'])\
            .food_options(body['food_options'])\
            .build()
        
        dao = EventDAO(table_name)
        created_event = dao.create_event(event_data)
        
        # Create Cognito user
        try:
            cognito.admin_create_user(
                UserPoolId=user_pool_id,
                Username=subdomain,
                TemporaryPassword=password,
                MessageAction='SUPPRESS'
            )
            
            # Set permanent password
            cognito.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=subdomain,
                Password=password,
                Permanent=True
            )
            
            # Add to users group
            cognito.admin_add_user_to_group(
                UserPoolId=user_pool_id,
                Username=subdomain,
                GroupName='users'
            )
        except ClientError as e:
            # Rollback event creation if user creation fails
            dao.delete_event(subdomain)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'User creation failed: {str(e)}'})
            }
        
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Event and user created successfully',
                'event': created_event
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
