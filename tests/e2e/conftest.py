import pytest
from utils.http_client import ApiClient


@pytest.fixture(scope="session")
def api_url():
    """API base URL - override with --api-url or API_URL env var"""
    import os
    return os.getenv("API_URL", "https://22tp7n0qdg.execute-api.us-east-2.amazonaws.com/v1")


@pytest.fixture(scope="session")
def admin_credentials():
    """Admin credentials for testing"""
    import os
    return {
        "username": os.getenv("ADMIN_USERNAME", "foo1"),
        "password": os.getenv("ADMIN_PASSWORD", "Pa$$word2")
    }


@pytest.fixture(scope="session")
def client(api_url):
    """HTTP client for API requests"""
    return ApiClient(api_url)


@pytest.fixture(scope="session")
def admin_client(admin_credentials, api_url):
    """Authenticated admin client"""
    client = ApiClient(api_url)
    client.login(admin_credentials["username"], admin_credentials["password"])
    return client

@pytest.fixture(scope="function")
def create_random_subdomain():
    """Helper function to create a random subdomain for testing"""
    import random
    import string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


@pytest.fixture(scope="function")
def event_data(create_random_subdomain):
    """Sample event data for testing"""
    return {
        "subdomain": create_random_subdomain,
        "guests_name": "John & Jane",
        "datetime_utc": "2026-06-15T18:00:00Z",
        "food_options": ["Vegetarian", "Vegan", "Regular"],
        "password": "TestPass123!",
        "message": "Join us for our special day!"
    }

@pytest.fixture(scope="function")
def event(admin_client, event_data):
    """Helper function to create an event for testing"""
    response = admin_client.create_event(**event_data)
    assert response.status_code == 201
    data = response.json()
    assert "event" in data
    assert data["event"]["subdomain"] == event_data["subdomain"]

    yield data

    response = admin_client.delete_event(event_data["subdomain"])
    assert response.status_code == 200


@pytest.fixture(scope="session")
def user_client(admin_client, api_url):
    """Authenticated user client with test event"""
    import uuid
    subdomain = f"e2e_test_event"
    password = "TestPass123!"
    
    admin_client.create_event(
        subdomain=subdomain,
        guests_name="Test User",
        datetime_utc="2026-12-31T20:00:00Z",
        food_options=["Vegetarian", "Regular"],
        password=password,
        message='foo'
    )
    
    client = ApiClient(api_url)
    client.login(subdomain, password)
    
    yield client
    
    admin_client.delete_event(subdomain)
