def test_get_invitation(user_client, client):
    """Test getting event and invitation info as a guest"""
    add_response = user_client.add_guest("Guest One", "+1", "5550001111", 2)
    guest = add_response.json()["guest"]

    response = client.get_invitation("e2e_test_event", guest["confirmation_code"])

    assert response.status_code == 200
    data = response.json()
    assert "event" in data
    assert "invitation" in data
    assert data["event"]["subdomain"] == "e2e_test_event"
    assert data["invitation"]["name"] == "Guest One"
    assert data["invitation"]["num_guests"] == 2
    assert data["invitation"]["confirmation_code"] == guest["confirmation_code"]


def test_get_invitation_invalid_code(client):
    """Test with invalid confirmation code returns 404"""
    response = client.get_invitation("e2e_test_event", "INVALID123")

    assert response.status_code == 404
    assert "Invitation not found" in response.json()["error"]


def test_get_invitation_invalid_event(client):
    """Test with non-existent event returns 404"""
    response = client.get_invitation("nonexistent_event", "WHATEVER1")

    assert response.status_code == 404
    assert "Event not found" in response.json()["error"]


def test_get_invitation_no_auth_required(api_url):
    """Test endpoint is accessible without authentication"""
    from utils.http_client import ApiClient
    unauthenticated = ApiClient(api_url)

    response = unauthenticated.get_invitation("e2e_test_event", "ANYCODE12")

    # Should get 404 (not found), not 401/403 (unauthorized)
    assert response.status_code == 404
