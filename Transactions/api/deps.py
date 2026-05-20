from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession 
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from db.session import AsyncSessionLocal
from core.security import decode_access_token
from core.config import load_config
from fastapi.exceptions import HTTPException
from types import SimpleNamespace
"""FAST API DEPENDECIES"""

config = load_config()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as Session:
         yield Session

# Token URL for OAuth2 - uses environment variable or defaults based on environment
AUTH_TOKEN_URL = config.get("AUTH_TOKEN_URL", "http://localhost:8081/auth/login")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=AUTH_TOKEN_URL)

def get_current_user(token: str = Depends(oauth2_scheme)):
    decoded = decode_access_token(encoded_token=token)

    if not decoded or decoded.user_id is None or decoded.sub is None:
        raise HTTPException(status_code=401,
                            detail='Not Authenticated',
                            headers={'WWW-Authenticate':'Bearer'}
                            )
    return SimpleNamespace(user_id=decoded.user_id, email=decoded.sub)

def dev_access()->bool:
    dev = True if load_config().get("DEVELOPMENT") == "True" else False
    return dev
