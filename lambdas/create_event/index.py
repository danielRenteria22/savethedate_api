import json
import os
import sys
import boto3
from botocore.exceptions import ClientError

from utils.event_dao import EventBuilder, EventDAO
from utils.response import cors_response

cognito = boto3.client('cognito-idp')
table_name = os.environ['TABLE_NAME']
user_pool_id = os.environ['USER_POOL_ID']

def handler(event, context):
    try:
        groups = event['requestContext']['authorizer'].get('groups', '')
        if 'admin' not in groups:
            return cors_response(403, {'error': 'Forbidden: Admin access required'})
        
        body = json.loads(event['body'])
        
        required = ['subdomain', 'guests_name', 'datetime_utc', 'food_options', 'password']
        missing = [f for f in required if f not in body]
        if missing:
            return cors_response(400, {'error': f'Missing fields: {", ".join(missing)}'})
        
        subdomain = body['subdomain']
        password = body['password']
        
        event_data = EventBuilder()\
            .subdomain(subdomain)\
            .guests_name(body['guests_name'])\
            .datetime_utc(body['datetime_utc'])\
            .food_options(body['food_options'])\
            .message(body.get('message'))\
            .build()
        
        dao = EventDAO(table_name)
        created_event = dao.create_event(event_data)
        
        try:
            cognito.admin_create_user(
                UserPoolId=user_pool_id,
                Username=subdomain,
                TemporaryPassword=password,
                MessageAction='SUPPRESS'
            )
            
            cognito.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=subdomain,
                Password=password,
                Permanent=True
            )
            
            cognito.admin_add_user_to_group(
                UserPoolId=user_pool_id,
                Username=subdomain,
                GroupName='users'
            )
        except ClientError as e:
            dao.delete_event(subdomain)
            return cors_response(400, {'error': f'User creation failed: {str(e)}'})
        
        return cors_response(201, {
            'message': 'Event and user created successfully',
            'event': created_event
        })
        
    except Exception as e:
        return cors_response(500, {'error': str(e)})
