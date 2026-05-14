import json
import os
import boto3
from utils.guest_dao import GuestDAO
from utils.enums import InvitationStatus
from utils.response import cors_response

sqs = boto3.client('sqs')
queue_url = os.environ['QUEUE_URL']
table_name = os.environ['TABLE_NAME']

SKIP_STATUSES = {InvitationStatus.SUCCESS, InvitationStatus.IN_PROGRESS}


def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')

        dao = GuestDAO(table_name)
        guests = dao.get_guests_by_event(subdomain)

        pending = [g for g in guests if g.invitation_status not in SKIP_STATUSES]

        if not pending:
            return cors_response(200, {'message': 'No pending invitations', 'queued': 0})

        for guest in pending:
            dao.update_guest(subdomain, guest.confirmation_code, {'invitation_status': InvitationStatus.IN_PROGRESS})
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps({
                    'event_id': subdomain,
                    'confirmation_code': guest.confirmation_code
                })
            )

        return cors_response(202, {'message': 'Invitations queued', 'queued': len(pending)})

    except Exception as e:
        return cors_response(500, {'error': str(e)})
