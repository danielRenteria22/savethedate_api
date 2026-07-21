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
    assert data["guest"]["invitation_status"] == 'NOT_SENT'


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


def test_mark_invitation_sent(user_client, guest_data):
    """Test manually marking invitation as sent"""
    add_response = user_client.add_guest(**guest_data)
    assert add_response.status_code == 201
    confirmation_code = add_response.json()["guest"]["confirmation_code"]
    assert add_response.json()["guest"]["invitation_status"] == 'NOT_SENT'

    # Mark as sent
    mark_response = user_client.mark_invitation_sent(confirmation_code)
    assert mark_response.status_code == 200
    assert mark_response.json()["invitation_status"] == 'SUCCESS'

    # Verify status is updated when listing guests
    list_response = user_client.list_guests()
    assert list_response.status_code == 200
    guests = list_response.json()["guests"]
    guest = next(g for g in guests if g["confirmation_code"] == confirmation_code)
    assert guest["invitation_status"] == 'SUCCESS'


def test_add_guest_batch_csv(user_client):
    """Test batch guest creation via CSV string matching real file schema with dummy values"""
    csv_content = (
        "NOMBRE,APELLIDO,CODIGO PAIS,WHATSAPP,No. PASES RECEPCIÓN,No. MESA\n"
        "Test,UserOne,52,5550000001,2,1\n"
        "Test,UserTwo,52,5550000002,2,2\n"
        "Test,UserThree,1,5550000003,2,1\n"
    )
    response = user_client.add_guest_batch(csv_data=csv_content)
    assert response.status_code == 201
    data = response.json()
    assert data["created_count"] == 3
    assert len(data["guests"]) == 3
    
    # Verify guest details
    user1 = next(g for g in data["guests"] if g["name"] == "Test UserOne")
    assert user1["phone_code"] == "+52"
    assert user1["phone_number"] == "5550000001"
    assert user1["num_guests"] == 2
    assert user1["table"] == "1"

    user3 = next(g for g in data["guests"] if g["name"] == "Test UserThree")
    assert user3["phone_code"] == "+1"


def test_add_guest_batch_json(user_client):
    """Test batch guest creation via JSON payload"""
    guests_list = [
        {"name": "Dummy Guest 1", "phone_code": "+52", "phone_number": "5551112222", "num_guests": 1, "table": "A"},
        {"name": "Dummy Guest 2", "phone_code": "+1", "phone_number": "5553334444", "num_guests": 3, "table": "B"}
    ]
    response = user_client.add_guest_batch(guests=guests_list)
    assert response.status_code == 201
    data = response.json()
    assert data["created_count"] == 2


