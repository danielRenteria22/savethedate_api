def test_get_my_event_success(user_client):
    """Test user can retrieve their own event"""
    response = user_client.get_my_event()
    assert response.status_code == 200
    data = response.json()
    assert "event" in data
    event = data["event"]
    assert event["subdomain"] == "e2e_test_event"
    assert event["guests_name"] == "Test User"
    assert event["datetime_utc"] == "2026-12-31T20:00:00Z"
    assert "food_options" in event
    assert "created_at" in event


def test_get_my_event_no_auth(client):
    """Test getting event without authentication returns 401"""
    response = client.get_my_event()
    assert response.status_code == 401
