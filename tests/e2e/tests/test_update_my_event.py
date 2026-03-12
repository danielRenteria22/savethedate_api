def test_update_my_event_message(user_client, admin_client):
    """Test user updating their event message"""
    response = user_client.update_my_event({"message": "Updated event message"})
    assert response.status_code == 200
    data = response.json()
    assert data["event"]["message"] == "Updated event message"
    
    # Verify persistence via admin list events
    events_response = admin_client.list_events()
    assert events_response.status_code == 200
    events = events_response.json()["events"]
    user_event = next((e for e in events if e.get("message") == "Updated event message"), None)
    assert user_event is not None


def test_update_my_event_food_options(user_client, admin_client):
    """Test user updating their event food options"""
    response = user_client.update_my_event({"food_options": ["Vegan", "Gluten-Free"]})
    assert response.status_code == 200
    data = response.json()
    assert data["event"]["food_options"] == ["Vegan", "Gluten-Free"]
    
    # Verify persistence via admin list events
    events_response = admin_client.list_events()
    assert events_response.status_code == 200
    events = events_response.json()["events"]
    user_event = next((e for e in events if e.get("food_options") == ["Vegan", "Gluten-Free"]), None)
    assert user_event is not None


def test_update_my_event_both_fields(user_client, admin_client):
    """Test user updating both message and food options"""
    response = user_client.update_my_event({
        "message": "New message",
        "food_options": ["Vegetarian", "Regular", "Vegan"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["event"]["message"] == "New message"
    assert data["event"]["food_options"] == ["Vegetarian", "Regular", "Vegan"]
    
    # Verify persistence
    events_response = admin_client.list_events()
    assert events_response.status_code == 200
    events = events_response.json()["events"]
    user_event = next((e for e in events if e.get("message") == "New message"), None)
    assert user_event is not None
    assert user_event["food_options"] == ["Vegetarian", "Regular", "Vegan"]


def test_update_my_event_invalid_fields(user_client):
    """Test user cannot update other fields"""
    response = user_client.update_my_event({"guests_name": "Hacker"})
    assert response.status_code == 400


def test_update_my_event_no_auth(client):
    """Test updating event without authentication"""
    response = client.update_my_event({"message": "Test"})
    assert response.status_code == 401
