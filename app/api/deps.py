from collections.abc import Generator
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from app.db.session import SessionLocal
from app.crud.user import get_user_by_email
from app.core.security import decode_access_token
from app.models.user  import User
from fastapi.exceptions import HTTPException
"""FAST API DEPENDECIES"""


def get_db()->Generator[Session,  None, None]:
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme))-> User:
    decoded = decode_access_token(encoded_token=token)

    if not decoded:
        raise HTTPException(status_code=401,
                            detail='Not Authenticated',
                            headers={'WWW-Authenticate':'Bearer'}
                            )
   
    current_user = get_user_by_email(db, email=decoded.sub)

    if not current_user:
        raise HTTPException(status_code=401,
                            detail='Credentials No Longer Valid',
                            headers={'WWW-Authenticate':'Bearer'}
                            )
    return current_user 
