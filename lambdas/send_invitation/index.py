import json
import os
import boto3

sqs = boto3.client('sqs')
queue_url = os.environ['QUEUE_URL']

def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        body = json.loads(event['body'])
        
        confirmation_code = body.get('confirmation_code')
        if not confirmation_code:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'confirmation_code is required'})
            }
        
        message = {
            'event_id': subdomain,
            'confirmation_code': confirmation_code
        }
        
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        
        return {
            'statusCode': 202,
            'body': json.dumps({'message': 'Invitation queued for sending'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
