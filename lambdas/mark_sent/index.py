import json
import os
from utils.guest_dao import GuestDAO
from utils.enums import InvitationStatus
from utils.response import cors_response

table_name = os.environ['TABLE_NAME']

def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        body = json.loads(event.get('body') or '{}')

        confirmation_code = body.get('confirmation_code')
        if not confirmation_code:
            return cors_response(400, {'error': 'confirmation_code is required'})

        dao = GuestDAO(table_name)
        guest = dao.get_guest(subdomain, confirmation_code)

        if not guest:
            return cors_response(404, {'error': 'Guest not found'})

        dao.update_guest(subdomain, confirmation_code, {'invitation_status': InvitationStatus.SUCCESS})

        return cors_response(200, {'message': 'Invitation marked as sent', 'invitation_status': InvitationStatus.SUCCESS})

    except Exception as e:
        return cors_response(500, {'error': str(e)})
