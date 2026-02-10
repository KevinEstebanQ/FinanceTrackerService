from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from typing import Literal


class TransactionCreate(BaseModel):
    amount: float = Field(gt=0, description="Transaction amount must be greater than 0")
    txn_type: Literal["income", "outcome"] = Field(description="Transaction type: income or outcome")
    desc: str = Field(min_length=1, description="Transaction description")
    transaction_date: datetime

class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0, description="Transaction amount must be greater than 0")
    txn_type: Optional[Literal["income", "outcome"]] = Field(None, description="Transaction type: income or outcome")
    desc: Optional[str] = Field(None, min_length=1, description="Transaction description")
    transaction_date: Optional[datetime] = None

class TransactionRead(TransactionCreate):
    id:int
    created_at:datetime