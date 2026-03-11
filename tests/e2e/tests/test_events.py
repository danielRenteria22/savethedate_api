import pytest

def test_create_event(event):
    """Test creating an event"""
    assert event["event"]["guests_name"] == "John & Jane"


def test_list_events(admin_client):
    """Test listing all events"""
    response = admin_client.list_events()
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert isinstance(data["events"], list)


def test_update_event(admin_client, event):
    """Test updating an event"""
    
    updates = {"guests_name": "Updated Name"}
    response = admin_client.update_event(event['event']['subdomain'], updates)
    assert response.status_code == 200
    data = response.json()
    assert data["event"]["guests_name"] == "Updated Name"


def test_delete_event(admin_client, event_data):
    """Test deleting an event"""
    admin_client.create_event(**event_data)
    
    response = admin_client.delete_event(event_data["subdomain"])
    assert response.status_code == 200


def test_create_event_unauthorized(client, event_data):
    """Test creating event without admin access"""
    response = client.create_event(**event_data)
    assert response.status_code in [401, 403]
