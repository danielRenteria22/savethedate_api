import boto3
from boto3.dynamodb.conditions import Key
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')

class Guest:
    def __init__(self, guest_id: str, event_id: str, name: str, phone_code: str, 
                 phone_number: str, num_guests: int, invitation_sent: bool, 
                 confirmed_assistance: bool, food_selection: Optional[str], created_at: str):
        self.guest_id = guest_id
        self.event_id = event_id
        self.name = name
        self.phone_code = phone_code
        self.phone_number = phone_number
        self.num_guests = num_guests
        self.invitation_sent = invitation_sent
        self.confirmed_assistance = confirmed_assistance
        self.food_selection = food_selection
        self.created_at = created_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Guest':
        return cls(
            guest_id=data['guest_id'],
            event_id=data['event_id'],
            name=data['name'],
            phone_code=data['phone_code'],
            phone_number=data['phone_number'],
            num_guests=data['num_guests'],
            invitation_sent=data['invitation_sent'],
            confirmed_assistance=data['confirmed_assistance'],
            food_selection=data.get('food_selection'),
            created_at=data['created_at']
        )

class GuestBuilder:
    def __init__(self):
        self._event_id = None
        self._name = None
        self._phone_code = None
        self._phone_number = None
        self._num_guests = None
        self._invitation_sent = False
        self._confirmed_assistance = False
        self._food_selection = None
    
    def event_id(self, event_id: str):
        self._event_id = event_id
        return self
    
    def name(self, name: str):
        self._name = name
        return self
    
    def phone_code(self, phone_code: str):
        self._phone_code = phone_code
        return self
    
    def phone_number(self, phone_number: str):
        self._phone_number = phone_number
        return self
    
    def num_guests(self, num_guests: int):
        self._num_guests = num_guests
        return self
    
    def invitation_sent(self, invitation_sent: bool):
        self._invitation_sent = invitation_sent
        return self
    
    def confirmed_assistance(self, confirmed_assistance: bool):
        self._confirmed_assistance = confirmed_assistance
        return self
    
    def food_selection(self, food_selection: str):
        self._food_selection = food_selection
        return self
    
    def build(self) -> Dict[str, Any]:
        guest_id = str(uuid.uuid4())
        return {
            'PK': f'EVENT#{self._event_id}',
            'SK': f'GUEST#{guest_id}',
            'guest_id': guest_id,
            'event_id': self._event_id,
            'name': self._name,
            'phone_code': self._phone_code,
            'phone_number': self._phone_number,
            'num_guests': self._num_guests,
            'invitation_sent': self._invitation_sent,
            'confirmed_assistance': self._confirmed_assistance,
            'food_selection': self._food_selection,
            'created_at': datetime.utcnow().isoformat()
        }

class GuestDAO:
    def __init__(self, table_name: str):
        self.table = dynamodb.Table(table_name)
    
    def create_guest(self, guest: Dict[str, Any]) -> Dict[str, Any]:
        self.table.put_item(Item=guest)
        return guest
    
    def get_guest(self, event_id: str, guest_id: str) -> Optional[Guest]:
        response = self.table.get_item(
            Key={'PK': f'EVENT#{event_id}', 'SK': f'GUEST#{guest_id}'}
        )
        item = response.get('Item')
        return Guest.from_dict(item) if item else None
    
    def get_guests_by_event(self, event_id: str) -> List[Guest]:
        response = self.table.query(
            KeyConditionExpression=Key('PK').eq(f'EVENT#{event_id}') & Key('SK').begins_with('GUEST#')
        )
        return [Guest.from_dict(item) for item in response.get('Items', [])]
    
    def update_guest(self, event_id: str, guest_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        update_expr = 'SET '
        expr_values = {}
        expr_names = {}
        
        for i, (key, value) in enumerate(updates.items()):
            attr_name = f'#attr{i}'
            attr_value = f':val{i}'
            update_expr += f'{attr_name} = {attr_value}, '
            expr_names[attr_name] = key
            expr_values[attr_value] = value
        
        update_expr = update_expr.rstrip(', ')
        
        response = self.table.update_item(
            Key={'PK': f'EVENT#{event_id}', 'SK': f'GUEST#{guest_id}'},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        return response['Attributes']
    
    def delete_guest(self, event_id: str, guest_id: str) -> None:
        self.table.delete_item(
            Key={'PK': f'EVENT#{event_id}', 'SK': f'GUEST#{guest_id}'}
        )
