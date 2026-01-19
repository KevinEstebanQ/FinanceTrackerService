from pydantic import BaseModel

class InfoResponse(BaseModel):
    desc: str
    author: str
    messageOfTheDay:str