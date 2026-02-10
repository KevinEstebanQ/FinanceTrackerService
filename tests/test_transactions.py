import pytest
from datetime import datetime


@pytest.fixture
def test_transaction(client, auth_headers):
    """Create a test transaction."""
    response = client.post(
        "/transactions",
        json={
            "amount": 100.50,
            "txn_type": "income",
            "desc": "Test transaction",
            "transaction_date": datetime.utcnow().isoformat()
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    return response.json()


def test_create_transaction(client, auth_headers):
    """Test creating a transaction."""
    response = client.post(
        "/transactions",
        json={
            "amount": 250.75,
            "txn_type": "outcome",
            "desc": "Grocery shopping",
            "transaction_date": datetime.utcnow().isoformat()
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == "250.75"
    assert data["txn_type"] == "outcome"
    assert data["desc"] == "Grocery shopping"
    assert "id" in data


def test_create_transaction_invalid_type(client, auth_headers):
    """Test creating a transaction with invalid type."""
    response = client.post(
        "/transactions",
        json={
            "amount": 100.0,
            "txn_type": "invalid",
            "desc": "Test",
            "transaction_date": datetime.utcnow().isoformat()
        },
        headers=auth_headers
    )
    assert response.status_code == 400


def test_create_transaction_negative_amount(client, auth_headers):
    """Test creating a transaction with negative amount."""
    response = client.post(
        "/transactions",
        json={
            "amount": -100.0,
            "txn_type": "income",
            "desc": "Test",
            "transaction_date": datetime.utcnow().isoformat()
        },
        headers=auth_headers
    )
    assert response.status_code == 400


def test_get_transactions(client, auth_headers, test_transaction):
    """Test getting list of transactions."""
    response = client.get("/transactions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_transaction_by_id(client, auth_headers, test_transaction):
    """Test getting a single transaction by ID."""
    transaction_id = test_transaction["id"]
    response = client.get(f"/transactions/{transaction_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == transaction_id
    assert data["desc"] == test_transaction["desc"]


def test_get_nonexistent_transaction(client, auth_headers):
    """Test getting a non-existent transaction."""
    response = client.get("/transactions/99999", headers=auth_headers)
    assert response.status_code == 404


def test_update_transaction(client, auth_headers, test_transaction):
    """Test updating a transaction."""
    transaction_id = test_transaction["id"]
    response = client.put(
        f"/transactions/{transaction_id}",
        json={
            "desc": "Updated description",
            "amount": 150.0
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["desc"] == "Updated description"
    assert data["amount"] == "150.00"


def test_update_transaction_invalid_type(client, auth_headers, test_transaction):
    """Test updating a transaction with invalid type."""
    transaction_id = test_transaction["id"]
    response = client.put(
        f"/transactions/{transaction_id}",
        json={
            "txn_type": "invalid"
        },
        headers=auth_headers
    )
    assert response.status_code == 404


def test_delete_transaction(client, auth_headers, test_transaction):
    """Test deleting a transaction."""
    transaction_id = test_transaction["id"]
    response = client.delete(f"/transactions/{transaction_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["ok"] is True
    
    # Verify it's deleted
    response = client.get(f"/transactions/{transaction_id}", headers=auth_headers)
    assert response.status_code == 404


def test_delete_nonexistent_transaction(client, auth_headers):
    """Test deleting a non-existent transaction."""
    response = client.delete("/transactions/99999", headers=auth_headers)
    assert response.status_code == 404


def test_transaction_isolation(client, auth_headers, db_session, test_user):
    """Test that users can only access their own transactions."""
    from app.core.security import hash_password
    from app.models.user import User
    
    # Create another user
    user2 = User(
        email="user2@example.com",
        hashed_password=hash_password("password123"),
        is_active=True
    )
    db_session.add(user2)
    db_session.commit()
    
    # Login as user2
    response = client.post(
        "/auth/login",
        data={"username": "user2@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    user2_token = response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    
    # Create transaction as user1
    response = client.post(
        "/transactions",
        json={
            "amount": 100.0,
            "txn_type": "income",
            "desc": "User1 transaction",
            "transaction_date": datetime.utcnow().isoformat()
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    transaction_id = response.json()["id"]
    
    # Try to access user1's transaction as user2
    response = client.get(f"/transactions/{transaction_id}", headers=user2_headers)
    assert response.status_code == 404
