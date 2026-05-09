import pytest


@pytest.fixture
def guest_data():
    """Sample guest data"""
    return {
        "name": "John Doe",
        "phone_code": "+1",
        "phone_number": "5551234567",
        "num_guests": 2
    }


def test_add_guest(user_client, guest_data):
    """Test adding a guest"""
    response = user_client.add_guest(**guest_data)
    assert response.status_code == 201
    data = response.json()
    assert "guest" in data
    assert data["guest"]["name"] == guest_data["name"]
    assert "confirmation_code" in data["guest"]
    assert data["guest"]["invitation_sent"] == False


def test_add_guest_default_invitation_flags(user_client, guest_data):
    """Test that civil_wedding_invitation and after_party_invitation default to False"""
    response = user_client.add_guest(**guest_data)
    assert response.status_code == 201
    data = response.json()
    assert data["guest"]["civil_wedding_invitation"] == False
    assert data["guest"]["after_party_invitation"] == False


def test_add_guest_with_civil_wedding_invitation(user_client, guest_data):
    """Test adding a guest with civil_wedding_invitation set to True"""
    response = user_client.add_guest(**guest_data, civil_wedding_invitation=True)
    assert response.status_code == 201
    data = response.json()
    assert data["guest"]["civil_wedding_invitation"] == True
    assert data["guest"]["after_party_invitation"] == False


def test_add_guest_with_after_party_invitation(user_client, guest_data):
    """Test adding a guest with after_party_invitation set to True"""
    response = user_client.add_guest(**guest_data, after_party_invitation=True)
    assert response.status_code == 201
    data = response.json()
    assert data["guest"]["civil_wedding_invitation"] == False
    assert data["guest"]["after_party_invitation"] == True


def test_add_guest_with_both_invitation_flags(user_client, guest_data):
    """Test adding a guest with both invitation flags set to True"""
    response = user_client.add_guest(**guest_data, civil_wedding_invitation=True, after_party_invitation=True)
    assert response.status_code == 201
    data = response.json()
    assert data["guest"]["civil_wedding_invitation"] == True
    assert data["guest"]["after_party_invitation"] == True


def test_update_guest_invitation_flags(user_client, guest_data):
    """Test updating civil_wedding_invitation and after_party_invitation via update_guest"""
    add_response = user_client.add_guest(**guest_data)
    confirmation_code = add_response.json()["guest"]["confirmation_code"]

    response = user_client.update_guest(confirmation_code, {
        "civil_wedding_invitation": True,
        "after_party_invitation": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["guest"]["civil_wedding_invitation"] == True
    assert data["guest"]["after_party_invitation"] == True


def test_list_guests(user_client, guest_data):
    """Test listing guests"""
    user_client.add_guest(**guest_data)
    
    response = user_client.list_guests()
    assert response.status_code == 200
    data = response.json()
    assert "guests" in data
    assert isinstance(data["guests"], list)


def test_list_guests_includes_invitation_flags(user_client, guest_data):
    """Test that list guests returns civil_wedding_invitation and after_party_invitation"""
    add_response = user_client.add_guest(**guest_data, civil_wedding_invitation=True, after_party_invitation=False)
    confirmation_code = add_response.json()["guest"]["confirmation_code"]

    response = user_client.list_guests()
    assert response.status_code == 200
    guests = response.json()["guests"]
    guest = next(g for g in guests if g["confirmation_code"] == confirmation_code)
    assert guest["civil_wedding_invitation"] == True
    assert guest["after_party_invitation"] == False


def test_update_guest(user_client, guest_data):
    """Test updating a guest"""
    add_response = user_client.add_guest(**guest_data)
    confirmation_code = add_response.json()["guest"]["confirmation_code"]
    
    updates = {"name": "Jane Doe", "num_guests": 3}
    response = user_client.update_guest(confirmation_code, updates)
    assert response.status_code == 200
    data = response.json()
    assert data["guest"]["name"] == "Jane Doe"


def test_update_confirmed_guest(user_client, guest_data):
    """Test updating a confirmed guest fails"""
    add_response = user_client.add_guest(**guest_data)
    confirmation_code = add_response.json()["guest"]["confirmation_code"]
    
    # Confirm guest
    user_client.update_guest(confirmation_code, {"confirmed_assistance": True})
    
    # Try to update
    response = user_client.update_guest(confirmation_code, {"name": "New Name"})
    assert response.status_code == 400


def test_delete_guest(user_client, guest_data):
    """Test deleting a guest"""
    add_response = user_client.add_guest(**guest_data)
    confirmation_code = add_response.json()["guest"]["confirmation_code"]
    
    response = user_client.delete_guest(confirmation_code)
    assert response.status_code == 200


def test_delete_nonexistent_guest(user_client):
    """Test deleting a nonexistent guest"""
    response = user_client.delete_guest("nonexistent-id")
    assert response.status_code == 404


def test_add_guest_missing_fields(user_client):
    """Test adding guest with missing fields"""
    response = user_client.add_guest(name="Test", phone_code="+1", phone_number="", num_guests=1)
    assert response.status_code == 400
