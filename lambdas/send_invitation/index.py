import json
import os
import boto3
from utils.response import cors_response

sqs = boto3.client('sqs')
queue_url = os.environ['QUEUE_URL']

def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        body = json.loads(event['body'])

        confirmation_code = body.get('confirmation_code')
        if not confirmation_code:
            return cors_response(400, {'error': 'confirmation_code is required'})

        message = {
            'event_id': subdomain,
            'confirmation_code': confirmation_code
        }

        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )

        return cors_response(202, {'message': 'Invitation queued for sending'})

    except Exception as e:
        return cors_response(500, {'error': str(e)})
