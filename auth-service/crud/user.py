from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from models.auth_session import AuthSession
from core.security import verify_password,hash_refresh_token, decode_access_token, create_access_token
from sqlalchemy import select, delete, update,Column
from fastapi.requests import Request
from schemas.auth import Token
from fastapi.exceptions import HTTPException
from datetime import datetime, timezone
from core.config import load_config
"""DB OPERATION LAYER"""

config = load_config()
async def get_user_by_email(db: AsyncSession, email: str)-> User | None:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()

#returns full auth Session for said refresh hash
async def query_auth_session(db:AsyncSession, hashed_refresh_token: str)->AuthSession:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    stmt = select(AuthSession) \
                .where((AuthSession.token_hash == hashed_refresh_token) &
                       (AuthSession.revoked_at.is_(None)) &
                       (AuthSession.expires_at > now))
    result = await db.execute(stmt)
    auth_session = result.scalar_one_or_none()
    if not auth_session:
        return None
    return auth_session

async def query_user_from_user_id(db:AsyncSession, user_id:int)-> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar()

async def update_auth_session(user:User, db:AsyncSession, request:Request)->Token:
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)

    stmt = update(AuthSession).where((AuthSession.user_id == user.id) &
                                     (AuthSession.revoked_at.is_(None)) &
                                     (AuthSession.expires_at > now)).values(revoked_at = now).execution_options(synchronize_session=False)
    await db.execute(stmt)

    from core.security import generate_refresh_token, hash_refresh_token
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
    email = user.email
    _id = user.id
    await db.commit()

    new_access = create_access_token(subject=email, user_id=_id)
    return Token(access_token=new_access, token_type="bearer", refresh_token=refresh_token)

async def authenticate_user(db:AsyncSession, email:str, password: str)->User | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not await verify_password(password, user.hashed_password):
        return None
    
    return user

async def verify_session_refresh(db:AsyncSession, refresh_token: str, request:Request)->Token:
    hashed = hash_refresh_token(refresh_token)
    auth_session = await query_auth_session(db=db, hashed_refresh_token=hashed)
    if not auth_session:
        return None
    user = await query_user_from_user_id(db=db, user_id=auth_session.user_id)
    if not user:
        return None
    elif not user.is_active:
        return None
    return await update_auth_session(db=db, user=user, request=request)

async def revoke_refresh_session(db: AsyncSession, refresh_token: str, user_id: int)->bool:
    hashed = hash_refresh_token(refresh_token)
    now = datetime.now(timezone.utc)
    stmt = update(AuthSession).where(
                                (AuthSession.user_id == user_id)
                                & (AuthSession.token_hash == hashed)
                                & (AuthSession.revoked_at.is_(None))
                                     ).values(revoked_at = now).execution_options(synchronize_session=False)
    result = await db.execute(statement=stmt)
    await db.commit()
    return True if result.rowcount > 0 else False

async def check_user_unique(db: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    response = await db.execute(stmt)
    await db.commit()
    return False if response.scalar() != None else True

