import json
import os
import boto3
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from utils.guest_dao import GuestDAO

table_name = os.environ['TABLE_NAME']
secret_name = os.environ['TWILIO_SECRET_NAME']
callback_url = os.environ['CALLBACK_URL']

secrets_client = boto3.client('secretsmanager')

def get_twilio_credentials():
    response = secrets_client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])
    return secret['account_sid'], secret['api_key_sid'], secret['api_key_secret'], secret['whatsapp_from']

def handler(event, context):
    dao = GuestDAO(table_name)
    account_sid, api_key_sid, api_key_secret, whatsapp_from = get_twilio_credentials()
    client = Client(api_key_sid, api_key_secret, account_sid)
    
    batch_item_failures = []
    
    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            event_id = message['event_id']
            confirmation_code = message['confirmation_code']
            
            guest = dao.get_guest(event_id, confirmation_code)
            if not guest:
                print(f"Guest not found: {event_id}/{confirmation_code}")
                continue
            
            to_number = f"whatsapp:{guest.phone_code}{guest.phone_number}"
            
            twilio_message = client.messages.create(
                from_=whatsapp_from,
                to=to_number,
                body=f"Hi {guest.name}! You're invited to our event. Confirmation code: {confirmation_code}",
                status_callback=f"{callback_url}?event_id={event_id}&confirmation_code={confirmation_code}"
            )
            
            if twilio_message.status in ['queued', 'sent', 'delivered']:
                dao.update_guest(event_id, confirmation_code, {'invitation_sent': True})
            else:
                print(f"Message failed with status: {twilio_message.status}")
                receive_count = int(record['attributes'].get('ApproximateReceiveCount', 0))
                if receive_count >= 3:
                    dao.update_guest(event_id, confirmation_code, {'invitation_sent_fatal_error': True})
                else:
                    batch_item_failures.append({'itemIdentifier': record['messageId']})
            
        except TwilioRestException as e:
            print(f"Twilio error: {e.code} - {e.msg}")
            receive_count = int(record['attributes'].get('ApproximateReceiveCount', 0))
            if receive_count >= 3:
                try:
                    message = json.loads(record['body'])
                    dao.update_guest(
                        message['event_id'], 
                        message['confirmation_code'], 
                        {'invitation_sent_fatal_error': True}
                    )
                except:
                    pass
            else:
                batch_item_failures.append({'itemIdentifier': record['messageId']})
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            receive_count = int(record['attributes'].get('ApproximateReceiveCount', 0))
            if receive_count >= 3:
                try:
                    message = json.loads(record['body'])
                    dao.update_guest(
                        message['event_id'], 
                        message['confirmation_code'], 
                        {'invitation_sent_fatal_error': True}
                    )
                except:
                    pass
            else:
                batch_item_failures.append({'itemIdentifier': record['messageId']})
    
    return {'batchItemFailures': batch_item_failures}
