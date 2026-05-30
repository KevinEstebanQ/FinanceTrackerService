from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from core.config import load_config
from core.security import create_access_token, generate_refresh_token, hash_refresh_token
from crud.user import authenticate_user, revoke_refresh_session, verify_session_refresh, check_user_unique
from models.auth_session import AuthSession
from core.security import hash_password
from models.user import User
from schemas.debug import DBVerify, DBVerify_in
from schemas.user import UserCreate, UserRead
from api.deps import get_db, get_current_user, dev_access
from schemas.auth import Token, AuthRefreshRead, LogoutRequest
from schemas.health import HealthResponse
from contextlib import asynccontextmanager
from cache.redis import get_redis
import redis.asyncio as aioredis


config = load_config()


#lifespan for FastApi app with redis
@asynccontextmanager
async def lifeSpan(app: FastAPI):
     app.state.pool = aioredis.ConnectionPool.from_url(
          config.get("REDIS_URL"),
          max_connections=50,
          decode_responses=True)
     yield
     await app.state.pool.aclose()
     

app = FastAPI(title="Finance Tracker Auth-API", 
              version="0.1.0",
              lifespan=lifeSpan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

##initialize DB
#init_db()

is_dev = config.get("DEVELOPMENT", "False") == "True"

@app.get("/health", response_model=HealthResponse)
def health_endpoint():
     enviroment = "Dev" if is_dev else "Prod"
     return HealthResponse(status="ok", service="Auth", version=app.version, enviroment=enviroment)

@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)  # Register a new user account with hashed credentials.
async def create_user(user_in: UserCreate, db:AsyncSession = Depends(get_db)):
    is_unique = await check_user_unique(db, user_in.email)
    if not is_unique:
            raise HTTPException(status_code=400, detail={"message": "user exists"})
    try:
        hashed_password = await hash_password(user_in.password)

        db_user = User(
            email = user_in.email,
            hashed_password = hashed_password,
            is_active=user_in.is_active,
            )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return UserRead(id=db_user.id,
                         email=db_user.email,
                           is_active=db_user.is_active,
                             created_at=db_user.created_at)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/auth/login", response_model=Token)  # Authenticate user and issue access and refresh tokens.
async def login(request:Request,form_data:OAuth2PasswordRequestForm = Depends(), db:AsyncSession = Depends(get_db)):
    """OAuth2 endpoint"""
    user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Email or Password",
            headers={"WWW-Authenticate":"Bearer"},
        )
    
    #token handling + refresh token
    access_token = create_access_token(subject=user.email, user_id=user.id)
    refresh_token = generate_refresh_token()
    hashed_refresh_token = hash_refresh_token(refresh_token)

    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)

    #make sure we update revoked at correctly
    stmt = update(AuthSession).where((AuthSession.user_id == user.id) &
                                     (AuthSession.revoked_at.is_(None)) &
                                     (AuthSession.expires_at > now)).values(revoked_at = now).execution_options(synchronize_session=False)
    await db.execute(statement=stmt)

    
    auth_session = AuthSession(
         user_id = user.id,
         token_hash = hashed_refresh_token,
         expires_at = now+timedelta(days=int(config.get('REFRESH_TOKEN_EXPIRE_DAYS'))),
         last_used_at = now,
         revoked_at = None,
         ip = request.client.host if request.client else None
    )
    db.add(auth_session)
    await db.commit()
    
    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token)

@app.get("/me", response_model=UserRead)  # Return the currently authenticated user's profile.
async def get_me(current_user: User = Depends(get_current_user))->User:
        return current_user

@app.get("/protected/ping")  # Protected heartbeat endpoint to verify auth enforcement.
async def enforce_auth(current_user: User = Depends(get_current_user)):
     return {"ok":True}

@app.post("/auth/refresh", response_model=Token)  # Exchange a valid refresh token for a new token set.
async def refresh_auth_session(request: Request, body: AuthRefreshRead, db:AsyncSession = Depends(get_db), user: User = Depends(get_current_user))->Token:
     token = await verify_session_refresh(db=db, refresh_token=body.refresh_token, request=request)
     if token is None:
          raise HTTPException(status_code=401, detail="unauthorized, incorrect token",
                              headers={"WWW-Authenticate": "bearer"})
     return token
     
@app.post("/auth/logout")  # Revoke an active refresh session for the authenticated user.
async def logout_request(body:LogoutRequest, current_user: User = Depends(get_current_user), 
                   db:AsyncSession = Depends(get_db))->dict:
    result = await revoke_refresh_session(db=db, 
                                    refresh_token=body.refresh_token, 
                                    user_id=current_user.id
                                    )
    if not result:
          raise HTTPException(status_code=401,
                              detail="Token Not Found",
                              headers={"WWW-Authenticate": "bearer"}
                              )
    return {"ok":result}
