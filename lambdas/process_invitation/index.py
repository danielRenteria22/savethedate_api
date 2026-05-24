import json
import os
import boto3
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from utils.guest_dao import GuestDAO
from utils.event_dao import EventDAO
from utils.enums import InvitationStatus

table_name = os.environ['TABLE_NAME']
secret_name = os.environ['TWILIO_SECRET_NAME']
callback_url = os.environ['CALLBACK_URL']
content_sid = os.environ['TWILIO_CONTENT_SID']
frontend_url = os.environ['FRONTEND_URL']

secrets_client = boto3.client('secretsmanager')

_secret = json.loads(secrets_client.get_secret_value(SecretId=secret_name)['SecretString'])
_client = Client(_secret['api_key_sid'], _secret['api_key_secret'], _secret['account_sid'])
_whatsapp_from = _secret['whatsapp_from']

def handler(event, context):
    dao = GuestDAO(table_name)
    event_dao = EventDAO(table_name)
    
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
            
            my_event = event_dao.get_event(event_id)
            if not my_event:
                print(f"Event not found: {event_id}")
                continue
            
            to_number = f"whatsapp:{guest.phone_code}{guest.phone_number}"
            link = f"{event_id}.{frontend_url}/{confirmation_code}"
            
            content_variables = json.dumps({
                "name": guest.name,
                "host_name": my_event.guests_name,
                "host_message": my_event.message or "",
                "link": link
            })
            
            twilio_message = _client.messages.create(
                from_=_whatsapp_from,
                to=to_number,
                content_sid=content_sid,
                content_variables=content_variables,
                status_callback=f"{callback_url}?event_id={event_id}&confirmation_code={confirmation_code}"
            )
            
            if twilio_message.status in ['delivered']:
                dao.update_guest(event_id, confirmation_code, {'invitation_status': InvitationStatus.SUCCESS})
            else:
                print(f"Message failed with status: {twilio_message.status}")
                receive_count = int(record['attributes'].get('ApproximateReceiveCount', 0))
                if receive_count >= 3:
                    dao.update_guest(event_id, confirmation_code, {'invitation_status': InvitationStatus.FAILED})
                else:
                    batch_item_failures.append({'itemIdentifier': record['messageId']})
            
        except TwilioRestException as e:
            print(f"Twilio error: {e.code} - {e.msg}")
            receive_count = int(record['attributes'].get('ApproximateReceiveCount', 0))
            if receive_count >= 3:
                try:
                    message = json.loads(record['body'])
                    dao.update_guest(message['event_id'], message['confirmation_code'], 
                                     {'invitation_status': InvitationStatus.FAILED})
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
                    dao.update_guest(message['event_id'], message['confirmation_code'], 
                                     {'invitation_status': InvitationStatus.FAILED})
                except:
                    pass
            else:
                batch_item_failures.append({'itemIdentifier': record['messageId']})
    
    return {'batchItemFailures': batch_item_failures}
