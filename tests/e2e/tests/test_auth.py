def test_login_success(client, admin_credentials):
    """Test successful login"""
    response = client.session.post(
        f"{client.base_url}/auth/login",
        json=admin_credentials
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "id_token" in data
    assert "refresh_token" in data


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.session.post(
        f"{client.base_url}/auth/login",
        json={"username": "invalid", "password": "wrong"}
    )
    assert response.status_code == 401
    assert "error" in response.json()


def test_login_missing_fields(client):
    """Test login with missing fields"""
    response = client.session.post(
        f"{client.base_url}/auth/login",
        json={"username": "test"}
    )
    assert response.status_code == 400
