import json
import boto3
import os

cognito = boto3.client('cognito-idp')
CLIENT_ID = os.environ["CLIENT_ID"]

def handler(event, context):
    try:
        body = json.loads(event['body'])
        
        cognito.respond_to_auth_challenge(
            ClientId=CLIENT_ID,
            ChallengeName='NEW_PASSWORD_REQUIRED',
            Session=body['session'],
            ChallengeResponses={
                'USERNAME': body['username'],
                'NEW_PASSWORD': body['newPassword']
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Password set successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
