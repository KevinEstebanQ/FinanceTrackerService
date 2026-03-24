from sqlalchemy.orm import Session
from sqlalchemy import Select, update,Delete
from models.transactions import Transaction
from schemas.transaction import TransactionSingle,TransactionGet
from datetime import datetime
from typing import List
import math

def create_new_transaction(db:Session,desc:str, amount:float, txn_type: str, transaction_date:datetime, user_id:int)->Transaction | None:
    if txn_type not in {"income", "outcome"}:
        return None
    if not desc:
        return None
    if amount is None or amount  <= 0 or math.isinf(amount):
        return None
    if transaction_date is None:
        return None

    new_transaction = Transaction(
        user_id = user_id,
        amount = amount,
        txn_type = txn_type,
        transaction_date = transaction_date,
        desc = desc
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction


def get_user_transactions(db:Session, user_id: int, limit: int = 10)->TransactionGet:
    stmt = Select(Transaction).where(Transaction.user_id == user_id).limit(limit)
    transaction = db.execute(stmt).scalars().all()
    return [TransactionSingle(amount=txn.amount, txn_type=txn.txn_type, desc=txn.desc, transaction_date=txn.transaction_date) for txn in transaction]