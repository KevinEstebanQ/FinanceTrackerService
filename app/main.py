from dotenv import dotenv_values
import os
from fastapi import FastAPI
from random import choice
from pydantic import BaseModel
from app.init_db import init_db
from sqlalchemy.orm import Session
from fastapi import Depends
from app.api.deps import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead



from app.schemas.health import HealthResponse
from app.schemas.info import InfoResponse



config = {
    **dotenv_values(".env.shared"),
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
        email=user_in.email,
        hashed_password = hashed_password,
        is_active=user_in.is_active,
        )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@app.post("/debug/verify")
def debug_verify(password: str, hashed:str):
    from app.core.security import verify_password
    return {"valid":verify_password(password,  hashed)}
