import pytest
from fastapi.testclient import TestClient
from main import app  # Import your FastAPI app

client = TestClient(app)

@pytest.fixture
def test_user():
    """Fixture to create a test user for signup tests."""
    return {"username": "testuser111", "password": "testpassword"}

def test_signup_success(test_user):
    """Test successful user signup."""
    response = client.post("/signup", json=test_user)
    print("response",response)
    assert response.status_code == 201
    assert response.json()["message"] == "User created successfully"

def test_signup_existing_user(test_user):
    """Test signing up with an existing username (should fail)."""
    client.post("/signup", json=test_user)  # First signup
    response = client.post("/signup", json=test_user)  # Second attempt
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already exists"


