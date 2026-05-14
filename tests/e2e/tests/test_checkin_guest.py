import pytest


@pytest.fixture
def guest_data():
    return {
        "name": "Checkin Test Guest",
        "phone_code": "+1",
        "phone_number": "5559999999",
        "num_guests": 2
    }


def test_checkin_guest(user_client, guest_data):
    """Test checking in a guest"""
    add_response = user_client.add_guest(**guest_data)
    assert add_response.status_code == 201
    confirmation_code = add_response.json()["guest"]["confirmation_code"]

    response = user_client.checkin_guest(confirmation_code)
    assert response.status_code == 200
    assert response.json()["message"] == "Guest checked in successfully"


def test_checkin_guest_twice_returns_already_checked_in(user_client, guest_data):
    """Test that checking in a guest twice returns already checked in"""
    add_response = user_client.add_guest(**guest_data)
    confirmation_code = add_response.json()["guest"]["confirmation_code"]

    user_client.checkin_guest(confirmation_code)
    response = user_client.checkin_guest(confirmation_code)
    assert response.status_code == 200
    assert response.json()["message"] == "Guest already checked in"


def test_checkin_nonexistent_guest(user_client):
    """Test checking in a guest that doesn't exist"""
    response = user_client.checkin_guest("NONEXISTENT")
    assert response.status_code == 404


def test_checkin_missing_guest_id(user_client):
    """Test checkin with missing guest_id"""
    response = user_client.session.post(
        f"{user_client.base_url}/host/checkin",
        json={}
    )
    assert response.status_code == 400


def test_list_guests_includes_checked_in(user_client, guest_data):
    """Test that list guests returns checked_in field"""
    add_response = user_client.add_guest(**guest_data)
    confirmation_code = add_response.json()["guest"]["confirmation_code"]

    # Before checkin
    response = user_client.list_guests()
    guests = response.json()["guests"]
    guest = next(g for g in guests if g["confirmation_code"] == confirmation_code)
    assert guest["checked_in"] == False

    # After checkin
    user_client.checkin_guest(confirmation_code)
    response = user_client.list_guests()
    guests = response.json()["guests"]
    guest = next(g for g in guests if g["confirmation_code"] == confirmation_code)
    assert guest["checked_in"] == True
