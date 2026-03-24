from collections.abc import Generator
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from db.session import SessionLocal
from core.security import decode_access_token
from core.config import load_config
from fastapi.exceptions import HTTPException
import httpx
from types import SimpleNamespace
"""FAST API DEPENDECIES"""

config = load_config()

def get_db()->Generator[Session,  None, None]:
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Token URL for OAuth2 - uses environment variable or defaults based on environment
AUTH_TOKEN_URL = config.get("AUTH_TOKEN_URL", "http://localhost:8081/auth/login")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=AUTH_TOKEN_URL)

def get_current_user(token: str = Depends(oauth2_scheme)):
    decoded = decode_access_token(encoded_token=token)

    if not decoded:
        raise HTTPException(status_code=401,
                            detail='Not Authenticated',
                            headers={'WWW-Authenticate':'Bearer'}
                            )
   
    # Call auth service to get user
    auth_service_url = config.get("AUTH_SERVICE_URL", "http://auth-service:8081")
    try:
        with httpx.Client() as client:
            response = client.get(f"{auth_service_url}/users/email/{decoded.sub}")
            if response.status_code == 200:
                user_data = response.json()
                # Convert dict to object for easier access
                return SimpleNamespace(**user_data)
            else:
                raise HTTPException(status_code=401,
                                    detail='Credentials No Longer Valid',
                                    headers={'WWW-Authenticate':'Bearer'}
                                    )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unavailable") 

def dev_access()->bool:
    dev = True if load_config().get("DEVELOPMENT") == "True" else False
    return dev
