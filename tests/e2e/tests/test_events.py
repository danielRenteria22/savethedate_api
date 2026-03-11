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
