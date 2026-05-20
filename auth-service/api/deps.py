from collections.abc import Generator
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from db.session import AsyncSessionLocal
from crud.user import get_user_by_email
from core.security import decode_access_token
from core.config import load_config
from models.user  import User
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import HTTPException
"""FAST API DEPENDECIES"""


async def get_db()->AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as Session:
         yield Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme))-> User:
    decoded = decode_access_token(encoded_token=token)

    if not decoded:
        raise HTTPException(status_code=401,
                            detail='Not Authenticated',
                            headers={'WWW-Authenticate':'Bearer'}
                            )
   
    current_user = await get_user_by_email(db, email=decoded.sub)

    if not current_user:
        raise HTTPException(status_code=401,
                            detail='Credentials No Longer Valid',
                            headers={'WWW-Authenticate':'Bearer'}
                            )
    if not current_user.is_active:
        raise HTTPException(status_code=403,
                            detail='Athenticated but Forbidden',
                            headers={'WWW-Authenticate':'Bearer'}
                            )
    return current_user 

def dev_access()->bool:
    dev = True if load_config().get("DEVELOPMENT") == "True" else False
    return dev