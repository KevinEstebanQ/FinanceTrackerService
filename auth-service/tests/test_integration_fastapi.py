import pytest_asyncio
import pytest
from core.security import decode_access_token, hash_refresh_token
from crud.user import check_refresh_revoked
from sqlalchemy.ext.asyncio import AsyncSession
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
    async def test_me_endpoint(self, test_client, logged_in_user: dict[str, any]):
        # Register and login to get a token
        access_token = logged_in_user["access_token"]
        user_info = await test_client.get("/me", headers={"Authorization": f"Bearer {access_token}"})
        assert user_info.status_code == 200

        assert decode_access_token(access_token).sub == user_info.json()["email"]

        assert access_token is not None


    @pytest.mark.asyncio
    async def test_refresh_token_cycle(self, test_client, logged_in_user: dict[str, any]):
        
        refresh_token = logged_in_user.get("refresh_token")
        auth_token = logged_in_user.get("access_token")
        ## promt a token refresh

        refresh_response = await test_client.post("/auth/refresh", json={"refresh_token": refresh_token},
                               headers={"Authorization":f"Bearer {auth_token}"})
        new_refresh = refresh_response.json().get("refresh_token", None)
        assert new_refresh is not None
        assert  new_refresh != refresh_token
    
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
    
    @pytest.mark.asyncio
    async def test_wrong_pass_status_code(self, test_client):
        registration_data = {"email": "test@email.com",
                             "password": "testpass1",
                             "is_active": True}
        
        register_response = await test_client.post("/users", json=registration_data)
        assert register_response.status_code == 201
        login_attempt = await test_client.post("/auth/login",
                                               data={"username": "test@email.com",
                                                     "password": "wrongpass"})
        assert login_attempt.status_code == 401

    @pytest.mark.asyncio
    async def test_no_access_token_me_endpoint(self, test_client):
        registration_data = {"email": "test@email.com",
                             "password": "testpass1",
                             "is_active": True}
        
        register_response = await test_client.post("/users", json=registration_data)
        token = "wrongtokendata123123123"
        me_response = await test_client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert me_response.status_code == 401
        

    @pytest.mark.asyncio
    async def test_refresh_revoked(self, test_client, test_session, logged_in_user: dict[str, any]):
        refresh_token = logged_in_user.get("refresh_token", None)
        access_token = logged_in_user.get("access_token", None)
        assert access_token is not None
        assert refresh_token is not None
        logout_response = await test_client.post("/auth/logout", json={"refresh_token": refresh_token},
                                                        headers={"Authorization":f"Bearer {access_token}"})
        assert logout_response.status_code == 200
        revoked = await check_refresh_revoked(test_session, refresh_token_old=refresh_token)
        assert revoked
    
    @pytest.mark.asyncio
    async def test_invalid_token_refresh(self, test_client, logged_in_user):
        token = logged_in_user.get("access_token", None)
        assert token is not None
        refresh_response = await test_client.post("/auth/refresh", 
                               headers={"Authorization": f"Bearer {token}"},
                               json={"refresh_token" : "invalidrefreshtoken"})
        assert refresh_response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_ignore_old_refresh_token(self, test_client, logged_in_user):
        access_token = logged_in_user.get("access_token", None)
        assert access_token is not None
        refresh_toke_old = logged_in_user.get("refresh_token", None)
        assert refresh_toke_old is not None
        refresh_response = await test_client.post("/auth/refresh", 
                                                   headers={"Authorization" : f"Bearer {access_token}"},
                                                   json={"refresh_token": refresh_toke_old})
        assert refresh_response.status_code == 200
        refresh_token_new = await test_client.post("/auth/refresh", 
                                                   headers={"Authorization" : f"Bearer {access_token}"},
                                                   json={"refresh_token": refresh_toke_old})
        assert refresh_token_new.status_code == 401

    @pytest.mark.asyncio
    async def test_me_inactive_user(self, test_client, test_session: AsyncSession):
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
        access_token = login_response.json().get("access_token", None)
        assert access_token is not None
        from sqlalchemy import update
        from models.user import User
        stmt = update(User).where(User.email == registration_data["email"]).values(is_active = False)
        result = await test_session.execute(statement=stmt)
        assert result.rowcount > 0
        failure_me_response = await test_client.get("/me", headers={"Authorization" : f"Bearer {access_token}"})
        assert failure_me_response.status_code == 403

    @pytest.mark.asyncio
    async def test_login_revokes_past_sessions(self, test_client,
                                               logged_in_user,
                                               registered_user):
        access_token = logged_in_user.get("access_token", None)
        refresh_token = logged_in_user.get("refresh_token", None)
        assert access_token is not None 
        assert refresh_token is not None
        login_response = await test_client.post("/auth/login", 
                                                data={"username":registered_user["email"],
                                                      "password": registered_user["password"]})
        assert login_response.status_code == 200
        new_token = login_response.json().get("access_token", None)
        assert new_token is not None
        response_old_refresh = await test_client.post("/auth/refresh", 
                                                      json={"refresh_token":refresh_token},
                                                      headers={"Authorization": f"Bearer {access_token}"})
        assert response_old_refresh.status_code == 401
    @pytest.mark.asyncio
    async def test_logout_with_revoked_refresh_token(self, test_client, logged_in_user):
        access_token = logged_in_user.get("access_token", None)
        refresh_token = logged_in_user.get("refresh_token", None)
        assert access_token is not None
        assert refresh_token is not None
        logout_response = await test_client.post("/auth/logout", json={"refresh_token": refresh_token},
                                                        headers={"Authorization":f"Bearer {access_token}"})
        assert logout_response.status_code == 200
        second_logout_response = await test_client.post("/auth/logout", json={"refresh_token": refresh_token},
                                                        headers={"Authorization":f"Bearer {access_token}"})
        assert second_logout_response.status_code == 401

    
    @pytest.mark.asyncio
    async def test_protected_ping(self, test_client, logged_in_user):
        access_token = logged_in_user.get("access_token", None)
        assert access_token is not None
        response = await test_client.get("/protected/ping", headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 200
        assert response.json() == {"ok": True}
    
    @pytest.mark.asyncio
    async def test_protected_ping_no_auth(self, test_client):
        response = await test_client.get("/protected/ping")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_health_endpoint_no_auth(self, test_client):
        response = await test_client.get("/health")
        assert response.status_code == 200



