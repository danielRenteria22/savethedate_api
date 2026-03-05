import boto3
from boto3.dynamodb.conditions import Key
from typing import Optional, List, Dict, Any
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

class Event:
    def __init__(self, subdomain: str, guests_name: str, datetime_utc: str, 
                 food_options: List[str], created_at: str):
        self.subdomain = subdomain
        self.guests_name = guests_name
        self.datetime_utc = datetime_utc
        self.food_options = food_options
        self.created_at = created_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        return cls(
            subdomain=data['subdomain'],
            guests_name=data['guests_name'],
            datetime_utc=data['datetime_utc'],
            food_options=data['food_options'],
            created_at=data['created_at']
        )

class EventBuilder:
    def __init__(self):
        self._subdomain = None
        self._guests_name = None
        self._datetime_utc = None
        self._food_options = []
    
    def subdomain(self, subdomain: str):
        self._subdomain = subdomain
        return self
    
    def guests_name(self, guests_name: str):
        self._guests_name = guests_name
        return self
    
    def datetime_utc(self, datetime_utc: str):
        self._datetime_utc = datetime_utc
        return self
    
    def food_options(self, food_options: List[str]):
        self._food_options = food_options
        return self
    
    def build(self) -> Dict[str, Any]:
        return {
            'PK': f'EVENT#{self._subdomain}',
            'SK': f'EVENT#{self._subdomain}',
            'subdomain': self._subdomain,
            'guests_name': self._guests_name,
            'datetime_utc': self._datetime_utc,
            'food_options': self._food_options,
            'created_at': datetime.utcnow().isoformat()
        }

class EventDAO:
    def __init__(self, table_name: str):
        self.table = dynamodb.Table(table_name)
    
    def create_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.table.put_item(Item=event)
        return event
    
    def get_event(self, subdomain: str) -> Optional[Event]:
        response = self.table.get_item(
            Key={'PK': f'EVENT#{subdomain}', 'SK': f'EVENT#{subdomain}'}
        )
        item = response.get('Item')
        return Event.from_dict(item) if item else None
    
    def update_event(self, subdomain: str, updates: Dict[str, Any]) -> Dict[str, Any]:
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
            Key={'PK': f'EVENT#{subdomain}', 'SK': f'EVENT#{subdomain}'},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        return response['Attributes']
    
    def delete_event(self, subdomain: str) -> None:
        self.table.delete_item(
            Key={'PK': f'EVENT#{subdomain}', 'SK': f'EVENT#{subdomain}'}
        )
    
    def list_events(self) -> List[Dict[str, Any]]:
        response = self.table.scan(
            FilterExpression='begins_with(PK, :pk)',
            ExpressionAttributeValues={':pk': 'EVENT#'}
        )
        return response.get('Items', [])
