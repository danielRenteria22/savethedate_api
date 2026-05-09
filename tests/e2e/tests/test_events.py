import pytest

def test_create_event(event):
    """Test creating an event"""
    assert event["event"]["guests_name"] == "John & Jane"
    assert event["event"]["message"] == "Join us for our special day!"


def test_list_events(admin_client, event):
    """Test listing all events returns only events with correct format"""
    response = admin_client.list_events()
    assert response.status_code == 200
    events = response.json()["events"]
    assert isinstance(events, list)
    assert len(events) > 0

    event_fields = {"subdomain", "guests_name", "datetime_utc", "food_options", "created_at"}
    guest_only_fields = {"confirmation_code", "phone_number", "phone_code", "num_guests", "invitation_sent"}

    for e in events:
        assert event_fields.issubset(e.keys()), f"Event missing expected fields: {e}"
        assert not guest_only_fields.intersection(e.keys()), f"Guest data found in event list: {e}"


def test_update_event(admin_client, event):
    """Test updating an event"""
    
    updates = {"guests_name": "Updated Name", "message": "Updated message"}
    response = admin_client.update_event(event['event']['subdomain'], updates)
    assert response.status_code == 200
    data = response.json()
    assert data["event"]["guests_name"] == "Updated Name"
    assert data["event"]["message"] == "Updated message"


def test_delete_event(admin_client, event_data):
    """Test deleting an event"""
    admin_client.create_event(**event_data)
    
    response = admin_client.delete_event(event_data["subdomain"])
    assert response.status_code == 200


def test_delete_event_with_guests(admin_client, event_data, api_url):
    """Test deleting an event also deletes its guests"""
    from utils.http_client import ApiClient
    
    # Create event
    admin_client.create_event(**event_data)
    
    # Login as event user and add guests
    user_client = ApiClient(api_url)
    user_client.login(event_data["subdomain"], event_data["password"])
    user_client.add_guest("Guest 1", "+1", "1234567890", 2)
    user_client.add_guest("Guest 2", "+1", "0987654321", 1)
    
    # Verify guests exist
    guests_response = user_client.list_guests()
    assert guests_response.status_code == 200
    assert len(guests_response.json()["guests"]) == 2
    
    # Delete event
    response = admin_client.delete_event(event_data["subdomain"])
    assert response.status_code == 200
    
    # Recreate event with same subdomain
    admin_client.create_event(**event_data)
    
    # Login and verify no guests exist
    new_user_client = ApiClient(api_url)
    new_user_client.login(event_data["subdomain"], event_data["password"])
    guests_response = new_user_client.list_guests()
    assert guests_response.status_code == 200
    assert len(guests_response.json()["guests"]) == 0
    
    # Cleanup
    admin_client.delete_event(event_data["subdomain"])


# Negative Tests - Missing Auth Token

def test_create_event_no_token(api_url, event_data):
    """Test creating event without auth token"""
    from utils.http_client import ApiClient
    client = ApiClient(api_url)
    response = client.create_event(**event_data)
    assert response.status_code == 401


def test_list_events_no_token(api_url):
    """Test listing events without auth token"""
    from utils.http_client import ApiClient
    client = ApiClient(api_url)
    response = client.list_events()
    assert response.status_code == 401


def test_update_event_no_token(api_url, event):
    """Test updating event without auth token"""
    from utils.http_client import ApiClient
    client = ApiClient(api_url)
    updates = {"guests_name": "Updated Name"}
    response = client.update_event(event['event']['subdomain'], updates)
    assert response.status_code == 401


def test_delete_event_no_token(api_url, event):
    """Test deleting event without auth token"""
    from utils.http_client import ApiClient
    client = ApiClient(api_url)
    response = client.delete_event(event['event']['subdomain'])
    assert response.status_code == 401


# Negative Tests - Invalid Auth Token

def test_create_event_invalid_token(api_url, event_data):
    """Test creating event with invalid auth token"""
    from utils.http_client import ApiClient
    client = ApiClient(api_url)
    client.session.headers.update({"Authorization": "Bearer invalid_token_123"})
    response = client.create_event(**event_data)
    assert response.status_code == 401


def test_list_events_invalid_token(api_url):
    """Test listing events with invalid auth token"""
    from utils.http_client import ApiClient
    client = ApiClient(api_url)
    client.session.headers.update({"Authorization": "Bearer invalid_token_123"})
    response = client.list_events()
    assert response.status_code == 401


def test_update_event_invalid_token(api_url, event):
    """Test updating event with invalid auth token"""
    from utils.http_client import ApiClient
    client = ApiClient(api_url)
    client.session.headers.update({"Authorization": "Bearer invalid_token_123"})
    updates = {"guests_name": "Updated Name"}
    response = client.update_event(event['event']['subdomain'], updates)
    assert response.status_code == 401


def test_delete_event_invalid_token(api_url, event):
    """Test deleting event with invalid auth token"""
    from utils.http_client import ApiClient
    client = ApiClient(api_url)
    client.session.headers.update({"Authorization": "Bearer invalid_token_123"})
    response = client.delete_event(event['event']['subdomain'])
    assert response.status_code == 401


# Negative Tests - Invalid Data

def test_create_event_missing_fields(admin_client):
    """Test creating event with missing required fields"""
    response = admin_client.session.post(
        f"{admin_client.base_url}/api/admin/event",
        json={"subdomain": "test"}
    )
    assert response.status_code == 400


def test_update_event_nonexistent(admin_client):
    """Test updating non-existent event"""
    response = admin_client.update_event("nonexistent123", {"guests_name": "Test"})
    assert response.status_code == 404


def test_delete_event_nonexistent(admin_client):
    """Test deleting non-existent event"""
    response = admin_client.delete_event("nonexistent123")
    assert response.status_code == 404
