from sqlalchemy.orm import Session
from app.models.transactions import Transaction
from datetime import datetime
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
    