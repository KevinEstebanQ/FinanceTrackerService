from sqlalchemy.orm import Session
from app.models.user import User
from app.models.auth_session import AuthSession
from app.core.security import verify_password,hash_refresh_token, verify_refresh_token, create_access_token
from sqlalchemy import select, delete, update,Column
from dotenv import load_dotenv,dotenv_values
from fastapi.requests import Request
from app.schemas.auth import Token
from fastapi.exceptions import HTTPException
"""DB OPERATION LAYER"""

config = {
    **dotenv_values(".env")
}
def get_user_by_email(db: Session, email: str)-> User | None:
    return db.query(User).filter(User.email == email).first()

#returns full auth Session for said refresh hash
def query_auth_session(db:Session, hashed_refresh_token: str)->AuthSession:
    from datetime import datetime, timezone
    now = datetime.utcnow()
    stmt = select(AuthSession) \
                .where((AuthSession.token_hash == hashed_refresh_token) &
                       (AuthSession.revoked_at.is_(None)) &
                       (AuthSession.expires_at > now))
    auth_session = db.execute(stmt).scalar()
    if not auth_session:
        raise HTTPException(
            status_code=401,
            detail="No Such Sessions",
            headers={"WWW-Authenticate": "bearer"}
        )
    return auth_session

def query_user_from_user_id(db:Session, user_id:int)-> User | None:
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar()
    return user

def update_auth_session(user:User, db:Session, request:Request)->Token:
    from datetime import datetime, timezone, timedelta
    now = datetime.utcnow()

    stmt = update(AuthSession).where((AuthSession.user_id == user.id) & 
                                     (AuthSession.revoked_at.is_(None)) & 
                                     (AuthSession.expires_at > now)).values(revoked_at = now)
    db.execute(stmt)

    from app.core.security import generate_refresh_token, hash_refresh_token
    refresh_token = generate_refresh_token()
    hashed_refresh_token = hash_refresh_token(refresh_token)
    auth_session = AuthSession(
         user_id = user.id,
         token_hash = hashed_refresh_token,
         expires_at = now+timedelta(days=int(config.get('REFRESH_TOKEN_EXPIRE_DAYS'))),
         last_used_at = now,
         revoked_at = None,
         ip = request.client.host if request.client else None
    )
    db.add(auth_session)
    db.commit()

    new_access = create_access_token(subject=user.email)
    return Token(access_token=new_access, token_type="bearer", refresh_token=refresh_token)

def authenticate_user(db:Session, email:str, password: str)->User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

def verify_session_refresh(db:Session, refresh_token: str, request:Request)->Token:
    hashed = hash_refresh_token(refresh_token)
    auth_session = query_auth_session(db=db, hashed_refresh_token=hashed)
    user = query_user_from_user_id(db=db, user_id=auth_session.user_id)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User does not Exist",
            headers={"WWWW-Authenticate": "bearer"}
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User is Authenticated but Forbidden",
            headers={"WWWW-Authenticate": "bearer"}
        )
    return update_auth_session(db=db, user=user, request=request)
    