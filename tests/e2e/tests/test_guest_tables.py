import pytest


@pytest.fixture
def guest_data():
    return {
        "name": "Table Test Guest",
        "phone_code": "+1",
        "phone_number": "5559999999",
        "num_guests": 2
    }


def test_add_guest_with_table(user_client, guest_data):
    """Test adding a guest with a table assignment"""
    response = user_client.add_guest(**guest_data, table="Mesa 5")
    assert response.status_code == 201
    assert response.json()["guest"]["table"] == "Mesa 5"


def test_add_guest_without_table_defaults_to_null(user_client, guest_data):
    """Test adding a guest without table defaults to null"""
    response = user_client.add_guest(**guest_data)
    assert response.status_code == 201
    assert response.json()["guest"]["table"] is None


def test_list_guests_includes_table(user_client, guest_data):
    """Test that list guests returns the table field"""
    add_response = user_client.add_guest(**guest_data, table="Mesa 1")
    confirmation_code = add_response.json()["guest"]["confirmation_code"]

    response = user_client.list_guests()
    assert response.status_code == 200
    guest = next(g for g in response.json()["guests"] if g["confirmation_code"] == confirmation_code)
    assert guest["table"] == "Mesa 1"


def test_update_guest_table(user_client, guest_data):
    """Test updating a guest's table"""
    add_response = user_client.add_guest(**guest_data)
    confirmation_code = add_response.json()["guest"]["confirmation_code"]

    response = user_client.update_guest(confirmation_code, {"table": "Mesa 10"})
    assert response.status_code == 200
    assert response.json()["guest"]["table"] == "Mesa 10"


def test_update_guest_table_to_null(user_client, guest_data):
    """Test clearing a guest's table assignment"""
    add_response = user_client.add_guest(**guest_data, table="Mesa 3")
    confirmation_code = add_response.json()["guest"]["confirmation_code"]

    response = user_client.update_guest(confirmation_code, {"table": None})
    assert response.status_code == 200
    assert response.json()["guest"]["table"] is None
