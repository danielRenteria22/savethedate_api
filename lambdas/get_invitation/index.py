import os
from utils.event_dao import EventDAO
from utils.guest_dao import GuestDAO
from utils.response import cors_response

table_name = os.environ['TABLE_NAME']


def handler(event, context):
    try:
        params = event.get('pathParameters') or {}
        event_id = params.get('event_id')
        confirmation_code = params.get('confirmation_code')

        if not event_id or not confirmation_code:
            return cors_response(400, {'error': 'event_id and confirmation_code are required'})

        event_dao = EventDAO(table_name)
        guest_dao = GuestDAO(table_name)

        my_event = event_dao.get_event(event_id)
        if not my_event:
            return cors_response(404, {'error': 'Event not found'})

        guest = guest_dao.get_guest(event_id, confirmation_code)
        if not guest:
            return cors_response(404, {'error': 'Invitation not found'})

        return cors_response(200, {
            'event': my_event.__dict__,
            'invitation': guest.__dict__
        })

    except Exception as e:
        return cors_response(500, {'error': str(e)})
