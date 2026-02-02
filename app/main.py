from dotenv import dotenv_values
import os
from fastapi import FastAPI, Header
from typing import Annotated
from random import choice
from pydantic import BaseModel
from app.init_db import init_db
from sqlalchemy.orm import Session
from sqlalchemy import delete,select, update
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.crud.user import authenticate_user, verify_session_refresh
from app.core.security import create_access_token, generate_refresh_token, hash_refresh_token, verify_refresh_token
from app.schemas.auth import Token, AuthRefreshRead
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.auth_session import AuthSession
from app.schemas.user import UserCreate, UserRead
from fastapi import Request
from app.schemas.health import HealthResponse
from app.schemas.info import InfoResponse
from app.schemas.debug import DBVerify, DBVerify_in


config = {
    **dotenv_values(".env")
}
app = FastAPI(title="Finance Tracker API", version="0.1.0")

##initialize DB
init_db()

is_dev = config.get("DEVELOPMENT", "False") == "True"


@app.get("/health", response_model=HealthResponse)
def health_Check():
    enviroment = "Dev" if is_dev else "Production"
    return HealthResponse(status="ok",
            service=app.title,
            version= app.version,
            enviroment = enviroment)

@app.get("/hello/{username}")
def say_hello(username: str):
    return {"message": f"Hello, {username}"}

@app.get("/info", response_model=InfoResponse)
def get_info():
    message =  ["This is your day, enjoy it", 
                "today might not be a good day, but I belive in you", 
                "Make the most from what you have been given"]
    return InfoResponse(desc= "this is the API for the finance tracker app",
                        author="Kevin Esteban Quiceno",
                        messageOfTheDay=choice(message))
        

@app.post("/users", response_model=UserRead)
def create_user(user_in: UserCreate, db:Session = Depends(get_db)):
    from app.core.security import hash_password
    hashed_password = hash_password(user_in.password)


    db_user = User(
        email = user_in.email,
        hashed_password = hashed_password,
        is_active=user_in.is_active,
        )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@app.post("/debug/verify",response_model=DBVerify)
def debug_verify(debug_in: DBVerify_in):
    
    from app.core.security import verify_password
    return DBVerify(validFlag=verify_password(debug_in.password,  debug_in.hashed_pasword))

@app.post("/auth/login", response_model=Token)
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

@app.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user))->User:
        return current_user

@app.get("/protected/ping")
def enforce_auth(current_user: User = Depends(get_current_user)):
     return {"ok":True}

@app.post("/auth/refresh", response_model=Token)
def refresh_auth_session(request: Request, body: AuthRefreshRead, db:Session = Depends(get_db))->Token:
     token = verify_session_refresh(db=db, refresh_token=body.refresh_token, request=request)
     return token
     
    