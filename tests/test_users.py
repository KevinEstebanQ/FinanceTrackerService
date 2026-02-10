import pytest


def test_get_users(client, auth_headers, test_user):
    """Test getting list of users."""
    response = client.get("/users", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_user_by_id(client, auth_headers, test_user):
    """Test getting a user by ID."""
    response = client.get(f"/users/{test_user.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


def test_get_nonexistent_user(client, auth_headers):
    """Test getting a non-existent user."""
    response = client.get("/users/99999", headers=auth_headers)
    assert response.status_code == 404


def test_users_require_auth(client):
    """Test that user endpoints require authentication."""
    response = client.get("/users")
    assert response.status_code == 401
    
    response = client.get("/users/1")
    assert response.status_code == 401
