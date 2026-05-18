import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from random import choice
from init_db import init_db
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from crud.transactions import create_new_transaction, get_user_transactions
from schemas.transaction import TransactionRead,TransactionCreate, TransactionGet
from api.deps import get_db, get_current_user, dev_access
from schemas.health import HealthResponse
from schemas.info import InfoResponse
from core.config import load_config


config = load_config()
app = FastAPI(title="Finance Tracker API", version="0.1.0")

##initialize DB
#init_db()

is_dev = config.get("DEVELOPMENT", "False") == "True"


@app.get("/health", response_model=HealthResponse)  # Service health and runtime environment status.
def health_Check():
    enviroment = "Dev" if is_dev else "Production"
    return HealthResponse(status="ok",
            service=app.title,
            version= app.version,
            enviroment = enviroment)

@app.get("/hello/{username}")  # Simple greeting endpoint for connectivity checks.
def say_hello(username: str):
    return {"message": f"Hello, {username}"}

@app.get("/info", response_model=InfoResponse)  # API metadata and motivational message of the day.
def get_info():
    message =  ["This is your day, enjoy it", 
                "today might not be a good day, but I belive in you", 
                "Make the most from what you have been given"]
    return InfoResponse(desc= "this is the API for the finance tracker app",
                        author="Kevin Esteban Quiceno",
                        messageOfTheDay=choice(message))
        

@app.post("/transactions", response_model=TransactionRead)  # Create a new transaction for the current user.
def new_transaction(body: TransactionCreate, 
                   db:Session = Depends(get_db), 
                   current_user = Depends(get_current_user)):
    txn = create_new_transaction(db, desc=body.desc, amount=body.amount, txn_type=body.txn_type, 
                            transaction_date=body.transaction_date, 
                            user_id=current_user.id)
    if txn is None:
         raise HTTPException(status_code=400, 
                             detail="Incorrect Transaction Data")
    else:
        return txn
    

@app.get("/transactions/user", response_model=TransactionGet)  # List all transactions for the current user.
def get_user_transaction(current_user = Depends(get_current_user), db: Session = Depends(get_db))-> TransactionGet:
    transactions = TransactionGet(transactions=get_user_transactions(db=db, user_id=current_user.id))
    return transactions
     

@app.get("/")  # Redirect root requests to interactive API documentation.
def home():
     return RedirectResponse(url="/docs")          
