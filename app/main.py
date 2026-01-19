from dotenv import load_dotenv, dotenv_values
import os
from fastapi import FastAPI
from random import choice
from pydantic import BaseModel
from app.init_db import init_db

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
        

@app.get("/multiply")
def multiply(a:int, b:int):
    return {"answer": a * b}