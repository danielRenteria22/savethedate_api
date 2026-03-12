import json
import os
from decimal import Decimal
from utils.guest_dao import GuestDAO

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
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'event_id and confirmation_code are required'})
            }
        
        if 'attending_guests' not in body or 'food_selection' not in body:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'attending_guests and food_selection are required'})
            }
        
        event_id = body['event_id']
        confirmation_code = body['confirmation_code']
        attending_guests = body['attending_guests']
        food_selection = body['food_selection']
        
        # Validate types
        if not isinstance(attending_guests, int) or attending_guests < 0:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'attending_guests must be a non-negative integer'})
            }
        
        if not isinstance(food_selection, list):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'food_selection must be a list'})
            }
        
        dao = GuestDAO(table_name)
        guest = dao.get_guest(event_id, confirmation_code)
        
        if not guest:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Guest not found'})
            }
        
        # Check if already confirmed
        if guest.confirmed_assistance:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Guest already confirmed'})
            }
        
        # Validate attending_guests doesn't exceed allowed
        if attending_guests > guest.num_guests:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'attending_guests cannot exceed {guest.num_guests}'})
            }
        
        # Validate food_selection length matches attending_guests
        if len(food_selection) != attending_guests:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'food_selection must have {attending_guests} items'})
            }
        
        # Update guest confirmation
        updated_guest = dao.update_guest(event_id, confirmation_code, {
            'confirmed_assistance': True,
            'attending_guests': attending_guests,
            'food_selection': food_selection
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps({'guest': updated_guest}, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
