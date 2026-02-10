from dotenv import dotenv_values
import os
from fastapi import FastAPI, Header
from typing import List
from random import choice
from pydantic import BaseModel
from app.init_db import init_db
from sqlalchemy.orm import Session
from sqlalchemy import delete,select, update
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.crud.user import authenticate_user, verify_session_refresh,revoke_refresh_session,cleanup_session, get_user_by_id, get_users
from app.crud.transactions import create_new_transaction, get_transaction, get_transactions, update_transaction, delete_transaction
from app.core.security import create_access_token, generate_refresh_token, hash_refresh_token, verify_refresh_token
from app.schemas.auth import Token, AuthRefreshRead, LogoutRequest
from app.schemas.transaction import TransactionRead,TransactionCreate, TransactionUpdate
from app.api.deps import get_db, get_current_user, dev_access, get_admin_user
from app.models.user import User
from app.models.transactions import Transaction
from app.models.auth_session import AuthSession
from app.schemas.user import UserCreate, UserRead
from fastapi import Request
from app.schemas.health import HealthResponse
from app.schemas.info import InfoResponse
from app.schemas.debug import DBVerify, DBVerify_in


config = {
    **dotenv_values(".env")
}

app = FastAPI(
    title="Finance Tracker API", 
    version="0.1.0",
    description="""
    A comprehensive finance tracking backend service built with FastAPI.
    
    ## Features
    
    * **User Management**: Create and manage user accounts with role-based access
    * **Authentication**: JWT-based authentication with refresh tokens
    * **Transaction Management**: Track income and outcome transactions
    * **Role-Based Access**: Admin and user roles with appropriate permissions
    
    ## Authentication
    
    Most endpoints require authentication. Use the `/auth/login` endpoint to obtain an access token.
    """,
    contact={
        "name": "Kevin Esteban Quiceno",
        "url": "https://github.com/KevinEstebanQ/FinanceTrackerService",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and service information endpoints"
        },
        {
            "name": "authentication",
            "description": "User authentication and authorization operations"
        },
        {
            "name": "users",
            "description": "User management operations (admin only for list/get)"
        },
        {
            "name": "transactions",
            "description": "Financial transaction operations"
        },
        {
            "name": "debug",
            "description": "Debug endpoints (development only)"
        },
    ]
)

##initialize DB
init_db()

is_dev = config.get("DEVELOPMENT", "False") == "True"


@app.get("/health", response_model=HealthResponse, tags=["health"],
         summary="Health check",
         description="Check if the service is running and get basic service information")
def health_Check():
    enviroment = "Dev" if is_dev else "Production"
    return HealthResponse(status="ok",
            service=app.title,
            version= app.version,
            enviroment = enviroment)

@app.get("/hello/{username}", tags=["health"],
         summary="Hello endpoint",
         description="A simple hello endpoint for testing")
def say_hello(username: str):
    return {"message": f"Hello, {username}"}

@app.get("/info", response_model=InfoResponse, tags=["health"],
         summary="Service information",
         description="Get service information and a motivational message")
def get_info():
    message =  ["This is your day, enjoy it", 
                "today might not be a good day, but I believe in you", 
                "Make the most from what you have been given"]
    return InfoResponse(desc= "this is the API for the finance tracker app",
                        author="Kevin Esteban Quiceno",
                        messageOfTheDay=choice(message))
        

@app.post("/users", response_model=UserRead, tags=["users"],
          summary="Create new user",
          description="Create a new user account. Default role is 'user'.")
def create_user(user_in: UserCreate, db:Session = Depends(get_db)):
    from app.core.security import hash_password
    hashed_password = hash_password(user_in.password)


    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(
        email = user_in.email,
        hashed_password = hashed_password,
        is_active=user_in.is_active,
        role="user",  # Always set to "user" for security - admins must be created by other admins
        )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@app.get("/users", response_model=List[UserRead], tags=["users"],
         summary="List all users (Admin only)",
         description="Get a list of all users in the system. Requires admin role.")
def list_users(skip: int = 0, 
               limit: int = 100,
               db: Session = Depends(get_db),
               current_user: User = Depends(get_admin_user)):
    users = get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user_id}", response_model=UserRead, tags=["users"],
         summary="Get user by ID (Admin only)",
         description="Get a specific user by their ID. Requires admin role.")
def get_user(user_id: int,
             db: Session = Depends(get_db),
             current_user: User = Depends(get_admin_user)):
    user = get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/debug/verify",response_model=DBVerify, tags=["debug"],
          summary="Verify password hash (Debug)",
          description="Debug endpoint to verify password hashing")
def debug_verify(debug_in: DBVerify_in):
    
    from app.core.security import verify_password
    return DBVerify(validFlag=verify_password(debug_in.password,  debug_in.hashed_pasword))

@app.post("/auth/login", response_model=Token, tags=["authentication"],
          summary="User login",
          description="Authenticate a user and receive access and refresh tokens")
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

@app.get("/me", response_model=UserRead, tags=["authentication"],
         summary="Get current user",
         description="Get information about the currently authenticated user")
def get_me(current_user: User = Depends(get_current_user))->User:
        return current_user

@app.get("/protected/ping", tags=["authentication"],
         summary="Test authentication",
         description="Test endpoint to verify authentication is working")
def enforce_auth(current_user: User = Depends(get_current_user)):
     return {"ok":True}

@app.post("/auth/refresh", response_model=Token, tags=["authentication"],
          summary="Refresh access token",
          description="Use a refresh token to obtain a new access token")
def refresh_auth_session(request: Request, body: AuthRefreshRead, db:Session = Depends(get_db))->Token:
     token = verify_session_refresh(db=db, refresh_token=body.refresh_token, request=request)
     return token
     
@app.post("/auth/logout", tags=["authentication"],
          summary="Logout user",
          description="Revoke a refresh token to log out the user")
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

@app.post("/debug/cleanup-sessions", tags=["debug"],
          summary="Cleanup expired sessions (Debug)",
          description="Debug endpoint to cleanup expired authentication sessions")
def debug_cleanup(current_user: User = Depends(get_current_user), db: Session = Depends(get_db), 
                  dev: bool = Depends(dev_access), grace_days:int = 2)->dict:
    if dev:
        from datetime import datetime
        now = datetime.utcnow()
        return {"deleted":cleanup_session(db=db, now=now, grace_days=grace_days)}
    else:
         raise HTTPException(status_code=401,
                             detail="User is Unauthorized", 
                             headers={"WWW-Authenticate":"bearer"}
                             )

@app.post("/transactions", response_model=TransactionRead, tags=["transactions"],
          summary="Create a new transaction",
          description="Create a new financial transaction. Type must be 'income' or 'outcome'.")
def new_transaction(body: TransactionCreate, 
                   db:Session = Depends(get_db), 
                   current_user:User = Depends(get_current_user)):
    txn = create_new_transaction(db, desc=body.desc, amount=body.amount, txn_type=body.txn_type, 
                            transaction_date=body.transaction_date, 
                            user_id=current_user.id)
    if txn is None:
         raise HTTPException(status_code=400, 
                             detail="Incorrect Transaction Data")
    else:
        return txn

@app.get("/transactions", response_model=List[TransactionRead], tags=["transactions"],
         summary="List user transactions",
         description="Get a list of all transactions for the authenticated user")
def list_transactions(skip: int = 0, 
                     limit: int = 100,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    transactions = get_transactions(db, user_id=current_user.id, skip=skip, limit=limit)
    return transactions

@app.get("/transactions/{transaction_id}", response_model=TransactionRead, tags=["transactions"],
         summary="Get transaction by ID",
         description="Get a specific transaction by ID. Users can only access their own transactions.")
def get_transaction_by_id(transaction_id: int,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    transaction = get_transaction(db, transaction_id=transaction_id, user_id=current_user.id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@app.put("/transactions/{transaction_id}", response_model=TransactionRead, tags=["transactions"],
         summary="Update a transaction",
         description="Update an existing transaction. Users can only update their own transactions.")
def update_transaction_by_id(transaction_id: int,
                             body: TransactionUpdate,
                             db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    transaction = update_transaction(
        db, 
        transaction_id=transaction_id, 
        user_id=current_user.id,
        desc=body.desc,
        amount=body.amount,
        txn_type=body.txn_type,
        transaction_date=body.transaction_date
    )
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found or invalid data")
    return transaction

@app.delete("/transactions/{transaction_id}", tags=["transactions"],
            summary="Delete a transaction",
            description="Delete a transaction. Users can only delete their own transactions.")
def delete_transaction_by_id(transaction_id: int,
                             db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    deleted = delete_transaction(db, transaction_id=transaction_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"ok": True, "message": "Transaction deleted successfully"}
     

