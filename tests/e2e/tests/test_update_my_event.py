def test_update_my_event_message(user_client):
    """Test user updating their event message"""
    response = user_client.update_my_event({"message": "Updated event message"})
    assert response.status_code == 200
    assert response.json()["event"]["message"] == "Updated event message"

    get_response = user_client.get_my_event()
    assert get_response.status_code == 200
    assert get_response.json()["event"]["message"] == "Updated event message"


def test_update_my_event_food_options(user_client):
    """Test user updating their event food options"""
    response = user_client.update_my_event({"food_options": ["Vegan", "Gluten-Free"]})
    assert response.status_code == 200
    assert response.json()["event"]["food_options"] == ["Vegan", "Gluten-Free"]

    get_response = user_client.get_my_event()
    assert get_response.status_code == 200
    assert get_response.json()["event"]["food_options"] == ["Vegan", "Gluten-Free"]


def test_update_my_event_both_fields(user_client):
    """Test user updating both message and food options"""
    response = user_client.update_my_event({
        "message": "New message",
        "food_options": ["Vegetarian", "Regular", "Vegan"]
    })
    assert response.status_code == 200
    event = response.json()["event"]
    assert event["message"] == "New message"
    assert event["food_options"] == ["Vegetarian", "Regular", "Vegan"]

    get_response = user_client.get_my_event()
    assert get_response.status_code == 200
    persisted = get_response.json()["event"]
    assert persisted["message"] == "New message"
    assert persisted["food_options"] == ["Vegetarian", "Regular", "Vegan"]


def test_update_my_event_invalid_fields(user_client):
    """Test user cannot update other fields"""
    response = user_client.update_my_event({"guests_name": "Hacker"})
    assert response.status_code == 400


def test_update_my_event_no_auth(client):
    """Test updating event without authentication"""
    response = client.update_my_event({"message": "Test"})
    assert response.status_code == 401
