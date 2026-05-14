import json
import os
from utils.guest_dao import GuestDAO
from utils.response import cors_response

table_name = os.environ['TABLE_NAME']


def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        body = json.loads(event.get('body') or '{}')
        guest_id = body.get('guest_id')

        if not guest_id:
            return cors_response(400, {'error': 'guest_id is required'})

        dao = GuestDAO(table_name)
        guest = dao.get_guest(subdomain, guest_id)

        if not guest:
            return cors_response(404, {'error': 'Guest not found'})

        if guest.checked_in:
            return cors_response(200, {'message': 'Guest already checked in'})

        dao.update_guest(subdomain, guest_id, {'checked_in': True})
        return cors_response(200, {'message': 'Guest checked in successfully'})

    except Exception as e:
        return cors_response(500, {'error': str(e)})
