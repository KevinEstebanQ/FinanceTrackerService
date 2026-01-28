from pydantic import BaseModel
from datetime import datetime

class Token(BaseModel):
    access_token:str
    token_type:str = 'bearer'

class TokenData(BaseModel):
    sub:str | None = None ##user identifier
    expire: int | None = None
    
