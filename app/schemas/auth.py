from pydantic import BaseModel
from datetime import datetime

class Token(BaseModel):
    access_token:str
    token_type:str = 'bearer'
    refresh_token: str

class TokenData(BaseModel):
    sub:str | None = None ##user identifier
    exp: int | None = None

class AuthRefreshRead(BaseModel):
    refresh_token:str

class AuthRefreshResponse(BaseModel):
    hashed_refresh_token: str
    new_jwt: str
    
