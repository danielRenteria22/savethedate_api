import boto3
from boto3.dynamodb.conditions import Key
from typing import Optional, List, Dict, Any
from datetime import datetime
import random
import string
from utils.enums import InvitationStatus

dynamodb = boto3.resource('dynamodb')

class Guest:
    def __init__(self, confirmation_code: str, event_id: str, name: str, phone_code: str, 
                 phone_number: str, num_guests: int, invitation_status: str,
                 confirmed_assistance: bool, attending_guests: Optional[int],
                 food_selection: Optional[List[str]], created_at: str,
                 civil_wedding_invitation: bool = False,
                 after_party_invitation: bool = False):
        self.confirmation_code = confirmation_code
        self.event_id = event_id
        self.name = name
        self.phone_code = phone_code
        self.phone_number = phone_number
        self.num_guests = num_guests
        self.invitation_status = invitation_status
        self.confirmed_assistance = confirmed_assistance
        self.attending_guests = attending_guests
        self.food_selection = food_selection
        self.created_at = created_at
        self.civil_wedding_invitation = civil_wedding_invitation
        self.after_party_invitation = after_party_invitation
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Guest':
        return cls(
            confirmation_code=data['confirmation_code'],
            event_id=data['event_id'],
            name=data['name'],
            phone_code=data['phone_code'],
            phone_number=data['phone_number'],
            num_guests=data['num_guests'],
            invitation_status=data.get('invitation_status', InvitationStatus.NOT_SENT),
            confirmed_assistance=data['confirmed_assistance'],
            attending_guests=data.get('attending_guests'),
            food_selection=data.get('food_selection'),
            created_at=data['created_at'],
            civil_wedding_invitation=data.get('civil_wedding_invitation', False),
            after_party_invitation=data.get('after_party_invitation', False)
        )

class GuestBuilder:
    def __init__(self):
        self._event_id = None
        self._name = None
        self._phone_code = None
        self._phone_number = None
        self._num_guests = None
        self._confirmed_assistance = False
        self._food_selection = None
        self._civil_wedding_invitation = False
        self._after_party_invitation = False
    
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
    
    def civil_wedding_invitation(self, civil_wedding_invitation: bool):
        self._civil_wedding_invitation = civil_wedding_invitation
        return self
    
    def after_party_invitation(self, after_party_invitation: bool):
        self._after_party_invitation = after_party_invitation
        return self
    
    def build(self) -> Dict[str, Any]:
        confirmation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return {
            'PK': f'EVENT#{self._event_id}',
            'SK': f'GUEST#{confirmation_code}',
            'confirmation_code': confirmation_code,
            'event_id': self._event_id,
            'name': self._name,
            'phone_code': self._phone_code,
            'phone_number': self._phone_number,
            'num_guests': self._num_guests,
            'invitation_status': InvitationStatus.NOT_SENT,
            'confirmed_assistance': self._confirmed_assistance,
            'food_selection': self._food_selection,
            'civil_wedding_invitation': self._civil_wedding_invitation,
            'after_party_invitation': self._after_party_invitation,
            'created_at': datetime.utcnow().isoformat()
        }

class GuestDAO:
    def __init__(self, table_name: str):
        self.table = dynamodb.Table(table_name)
    
    def create_guest(self, guest: Dict[str, Any]) -> Dict[str, Any]:
        self.table.put_item(Item=guest)
        return guest
    
    def get_guest(self, event_id: str, confirmation_code: str) -> Optional[Guest]:
        response = self.table.get_item(
            Key={'PK': f'EVENT#{event_id}', 'SK': f'GUEST#{confirmation_code}'}
        )
        item = response.get('Item')
        return Guest.from_dict(item) if item else None
    
    def get_guests_by_event(self, event_id: str) -> List[Guest]:
        response = self.table.query(
            KeyConditionExpression=Key('PK').eq(f'EVENT#{event_id}') & Key('SK').begins_with('GUEST#')
        )
        return [Guest.from_dict(item) for item in response.get('Items', [])]
    
    def update_guest(self, event_id: str, confirmation_code: str, updates: Dict[str, Any]) -> Dict[str, Any]:
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
            Key={'PK': f'EVENT#{event_id}', 'SK': f'GUEST#{confirmation_code}'},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        return response['Attributes']
    
    def delete_guest(self, event_id: str, confirmation_code: str) -> None:
        self.table.delete_item(
            Key={'PK': f'EVENT#{event_id}', 'SK': f'GUEST#{confirmation_code}'}
        )
