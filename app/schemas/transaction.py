from pydantic import BaseModel
from datetime import datetime

class TransactionCreate(BaseModel):
    amount: float
    txn_type: str
    desc: str
    transaction_date: datetime

class TransactionRead(TransactionCreate):
    id:int
    created_at:datetime