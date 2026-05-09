import pytest
import time


def test_send_invitation(user_client):
    """Test sending WhatsApp invitation to a guest"""
    
    # Create a guest first
    response = user_client.add_guest(
        name="Daniel Test",
        phone_code="+52",
        phone_number="6391790331",
        num_guests=2
    )
    assert response.status_code == 201
    
    guest = response.json()["guest"]
    confirmation_code = guest["confirmation_code"]
    
    # Send invitation
    response = user_client.send_invitation(confirmation_code)
    
    assert response.status_code == 202
    assert "message" in response.json()
    
    print(f"\n✓ Invitation queued for guest: {guest['name']}")
    print(f"  Confirmation code: {confirmation_code}")
    print(f"  Phone: {guest['phone_code']}{guest['phone_number']}")


