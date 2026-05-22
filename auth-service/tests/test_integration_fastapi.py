import pytest_asyncio
import pytest

class TestAuthServiceIntegration:
    """Integration tests for the Auth Service using FastAPI and an async test client."""

    @pytest.mark.asyncio
    async def test_user_registration(self, test_client):
        # Test user registration
        registration_data = {
            "email": "testuser@example.com",
            "password": "testpassword",
            "is_active": True
        }
        response = await test_client.post("/users", json=registration_data)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_user_registration_and_login(self, test_client):  
        registration_data = {
            "email": "testuser@example.com",
            "password": "testpassword",
            "is_active": True
        }
        await test_client.post("/users", json=registration_data)
        # Test user login
        login_response = await test_client.post("/auth/login", data= {"username": "testuser@example.com",
                                                                       "password": "testpassword"})
        assert login_response.status_code == 200
