from pydantic import BaseModel

class DBVerify(BaseModel):
    validFlag:bool

class DBVerify_in(BaseModel):
    password: str
    hashed_pasword:str

    