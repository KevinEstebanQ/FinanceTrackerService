import pytest_asyncio
import pytest
from core.security import decode_access_token

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

    @pytest.mark.asyncio
    async def test_me_endpoint(self, test_client):
        # Register and login to get a token
        registration_data = {
            "email": "testuser@example.com",
            "password": "testpassword",
            "is_active": True}
        await test_client.post("/users", json=registration_data)
        login_response = await test_client.post("/auth/login", data= {"username": "testuser@example.com",
                                                                       "password": "testpassword"})
        access_token = login_response.json()["access_token"]
        user_info = await test_client.get("/me", headers={"Authorization": f"Bearer {access_token}"})
        assert user_info.status_code == 200

        assert decode_access_token(access_token).sub == user_info.json()["email"]

        assert access_token is not None

    @pytest.mark.asyncio
    async def test_refresh_token_cycle(self, test_client):
        registration_data = {"email": "test@email.com",
                             "password": "testpass1",
                             "is_active": True}
        await test_client.post("/users", json=registration_data)
        login_response = await test_client.post("auth/login", data={"username": "test@email.com",
                                                                "password": "testpass1"})
        
        refresh_token = login_response.json().get("refresh_token")
        auth_token = login_response.json().get("access_token")
        ## promt a token refresh

        new_refresh = await test_client.post("/auth/refresh", json={"refresh_token": refresh_token},
                               headers={"Authorization":f"Bearer {auth_token}"})

        assert new_refresh != refresh_token
    
    @pytest.mark.asyncio
    async def test_duplicate_user_status_code(self, test_client):
        #create new user
        registration_data = {"email": "test@email.com",
                             "password": "testpass1",
                             "is_active": True}
        await test_client.post("/users", json=registration_data)

        ## test for correct duplicate handling
        response = await test_client.post("/users", json=registration_data)
        assert response.status_code == 400
    
