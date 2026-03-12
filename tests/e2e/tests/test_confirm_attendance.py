def test_confirm_attendance(user_client, client, event_data):
    """Test confirming attendance"""
    # Add a guest
    add_response = user_client.add_guest("John Doe", "+1", "5551234567", 3)
    guest = add_response.json()["guest"]
    
    # Confirm attendance (public endpoint, no auth)
    response = client.confirm_attendance(
        event_id="e2e_test_event",
        confirmation_code=guest["confirmation_code"],
        attending_guests=2,
        food_selection=["Vegetarian", "Regular"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["guest"]["confirmed_assistance"] == True
    assert data["guest"]["attending_guests"] == 2
    assert data["guest"]["food_selection"] == ["Vegetarian", "Regular"]
    
    # Verify confirmation persisted
    guests_response = user_client.list_guests()
    assert guests_response.status_code == 200
    guests = guests_response.json()["guests"]
    confirmed_guest = next(g for g in guests if g["confirmation_code"] == guest["confirmation_code"])
    assert confirmed_guest["confirmed_assistance"] == True
    assert confirmed_guest["attending_guests"] == 2
    assert confirmed_guest["food_selection"] == ["Vegetarian", "Regular"]


def test_confirm_attendance_twice(user_client, client, event_data):
    """Test guest cannot confirm twice"""
    add_response = user_client.add_guest("Alice Brown", "+1", "5553334444", 2)
    guest = add_response.json()["guest"]
    
    # First confirmation
    response = client.confirm_attendance(
        event_id="e2e_test_event",
        confirmation_code=guest["confirmation_code"],
        attending_guests=2,
        food_selection=["Vegetarian", "Regular"]
    )
    assert response.status_code == 200
    
    # Second confirmation attempt
    response = client.confirm_attendance(
        event_id="e2e_test_event",
        confirmation_code=guest["confirmation_code"],
        attending_guests=1,
        food_selection=["Vegan"]
    )
    assert response.status_code == 400


def test_confirm_attendance_exceeds_limit(user_client, client, event_data):
    """Test confirming more guests than allowed"""
    add_response = user_client.add_guest("Jane Doe", "+1", "5559876543", 2)
    guest = add_response.json()["guest"]
    
    response = client.confirm_attendance(
        event_id="e2e_test_event",
        confirmation_code=guest["confirmation_code"],
        attending_guests=3,
        food_selection=["Vegetarian", "Regular", "Vegan"]
    )
    
    assert response.status_code == 400


def test_confirm_attendance_mismatched_food_selection(user_client, client, event_data):
    """Test food selection length doesn't match attending guests"""
    add_response = user_client.add_guest("Bob Smith", "+1", "5551112222", 3)
    guest = add_response.json()["guest"]
    
    response = client.confirm_attendance(
        event_id="e2e_test_event",
        confirmation_code=guest["confirmation_code"],
        attending_guests=2,
        food_selection=["Vegetarian"]
    )
    
    assert response.status_code == 400


def test_confirm_attendance_invalid_code(client, event_data):
    """Test confirming with invalid confirmation code"""
    response = client.confirm_attendance(
        event_id="e2e_test_event",
        confirmation_code="INVALID123",
        attending_guests=1,
        food_selection=["Regular"]
    )
    
    assert response.status_code == 404
