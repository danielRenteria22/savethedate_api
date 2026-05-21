import json
import os
from decimal import Decimal
from utils.guest_dao import GuestDAO
from utils.response import cors_response

table_name = os.environ['TABLE_NAME']

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError

def handler(event, context):
    try:
        body = json.loads(event['body'])
        
        # Validate required fields
        if 'event_id' not in body or 'confirmation_code' not in body:
            return cors_response(400, {'error': 'event_id and confirmation_code are required'})
        
        if 'attending_guests' not in body:
            return cors_response(400, {'error': 'attending_guests is required'})
        
        event_id = body['event_id']
        confirmation_code = body['confirmation_code']
        attending_guests = body['attending_guests']
        food_selection = body.get('food_selection')
        
        # Validate types
        if not isinstance(attending_guests, int) or attending_guests < 0:
            return cors_response(400, {'error': 'attending_guests must be a non-negative integer'})
        
        if food_selection is not None and not isinstance(food_selection, list):
            return cors_response(400, {'error': 'food_selection must be a list or null'})
        
        dao = GuestDAO(table_name)
        guest = dao.get_guest(event_id, confirmation_code)
        
        if not guest:
            return cors_response(404, {'error': 'Guest not found'})
        
        # Check if already confirmed
        if guest.confirmed_assistance:
            return cors_response(400, {'error': 'Guest already confirmed'})
        
        # Validate attending_guests doesn't exceed allowed
        if attending_guests > guest.num_guests:
            return cors_response(400, {'error': f'attending_guests cannot exceed {guest.num_guests}'})
        
        # Validate food_selection length matches attending_guests
        if food_selection is not None and len(food_selection) != attending_guests:
            return cors_response(400, {'error': f'food_selection must have {attending_guests} items'})
        
        # Update guest confirmation
        updated_guest = dao.update_guest(event_id, confirmation_code, {
            'confirmed_assistance': True,
            'attending_guests': attending_guests,
            'food_selection': food_selection
        })
        
        response = cors_response(200, {'guest': updated_guest})
        response['body'] = json.dumps({'guest': updated_guest}, default=decimal_default)
        return response
        
    except Exception as e:
        return cors_response(500, {'error': str(e)})
