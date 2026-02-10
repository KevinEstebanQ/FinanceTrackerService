from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransactionCreate(BaseModel):
    amount: float
    txn_type: str
    desc: str
    transaction_date: datetime

class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    txn_type: Optional[str] = None
    desc: Optional[str] = None
    transaction_date: Optional[datetime] = None

class TransactionRead(TransactionCreate):
    id:int
    created_at:datetime