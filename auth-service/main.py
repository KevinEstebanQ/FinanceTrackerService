from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import update
from init_db import init_db
from core.config import load_config
from core.security import create_access_token, generate_refresh_token, hash_refresh_token
from crud.user import authenticate_user, revoke_refresh_session, verify_session_refresh
from models.auth_session import AuthSession
from models.user import User
from schemas.debug import DBVerify, DBVerify_in
from schemas.user import UserCreate, UserRead
from api.deps import get_db, get_current_user, dev_access
from schemas.auth import Token, AuthRefreshRead, LogoutRequest
from schemas.health import HealthResponse


config = load_config()
app = FastAPI(title="Finance Tracker Auth-API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

##initialize DB
init_db()

is_dev = config.get("DEVELOPMENT", "False") == "True"

@app.get("/health", response_model=HealthResponse)
def health_endpoint():
     enviroment = "Dev" if is_dev else "Prod"
     return HealthResponse(status="ok", service="Auth", version=app.version, enviroment=enviroment)

@app.post("/users", response_model=UserRead)  # Register a new user account with hashed credentials.
def create_user(user_in: UserCreate, db:Session = Depends(get_db)):
    try:
        from core.security import hash_password
        hashed_password = hash_password(user_in.password)

        db_user = User(
            email = user_in.email,
            hashed_password = hashed_password,
            is_active=user_in.is_active,
            )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return UserRead(id=db_user.id, email=db_user.email, is_active=db_user.is_active, created_at=db_user.created_at)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debug/verify",response_model=DBVerify)  # Debug endpoint to validate password-hash matching.
def debug_verify(debug_in: DBVerify_in):
    
    from core.security import verify_password
    return DBVerify(validFlag=verify_password(debug_in.password,  debug_in.hashed_pasword))

@app.post("/auth/login", response_model=Token)  # Authenticate user and issue access and refresh tokens.
def login(request:Request,form_data:OAuth2PasswordRequestForm = Depends(), db:Session = Depends(get_db)):
    """OAuth2 endpoint"""
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Email or Password",
            headers={"WWW-Authenticate":"Bearer"},
        )
    
    #token handling + refresh token
    access_token = create_access_token(subject=user.email)
    refresh_token = generate_refresh_token()
    hashed_refresh_token = hash_refresh_token(refresh_token)

    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)

    #make sure we update revoked at correctly
    stmt = update(AuthSession).where((AuthSession.user_id == user.id) & 
                                     (AuthSession.revoked_at.is_(None)) & 
                                     (AuthSession.expires_at > now)).values(revoked_at = now)
    db.execute(statement=stmt)

    
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
    
    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token)

@app.get("/me", response_model=UserRead)  # Return the currently authenticated user's profile.
def get_me(current_user: User = Depends(get_current_user))->User:
        return current_user

@app.get("/protected/ping")  # Protected heartbeat endpoint to verify auth enforcement.
def enforce_auth(current_user: User = Depends(get_current_user)):
     return {"ok":True}

@app.post("/auth/refresh", response_model=Token)  # Exchange a valid refresh token for a new token set.
def refresh_auth_session(request: Request, body: AuthRefreshRead, db:Session = Depends(get_db))->Token:
     token = verify_session_refresh(db=db, refresh_token=body.refresh_token, request=request)
     if not token:
         raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
     return token
     
@app.post("/auth/logout")  # Revoke an active refresh session for the authenticated user.
def logout_request(body:LogoutRequest, current_user: User = Depends(get_current_user), 
                   db:Session = Depends(get_db))->dict:
    result = revoke_refresh_session(db=db, 
                                    refresh_token=body.refresh_token, 
                                    user_id=current_user.id
                                    )
    if not result:
          raise HTTPException(status_code=401,
                              detail="Token Not Found",
                              headers={"WWW-Authenticate": "bearer"}
                              )
    return {"ok":result}

@app.get("/users/email/{email}", response_model=UserRead)  # Get user by email (for inter-service communication).
def get_user_by_email_endpoint(email: str, db: Session = Depends(get_db)):
    from crud.user import get_user_by_email
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user