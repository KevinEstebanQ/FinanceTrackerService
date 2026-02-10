from sqlalchemy.orm import Session
from app.models.transactions import Transaction
from datetime import datetime
import math
from typing import List, Optional

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

def get_transaction(db: Session, transaction_id: int, user_id: int) -> Optional[Transaction]:
    return db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()

def get_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
    return db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).offset(skip).limit(limit).all()

def update_transaction(db: Session, transaction_id: int, user_id: int, 
                       desc: Optional[str] = None, 
                       amount: Optional[float] = None, 
                       txn_type: Optional[str] = None,
                       transaction_date: Optional[datetime] = None) -> Optional[Transaction]:
    transaction = get_transaction(db, transaction_id, user_id)
    if not transaction:
        return None
    
    if desc is not None:
        if not desc:
            return None
        transaction.desc = desc
    
    if amount is not None:
        if amount <= 0 or math.isinf(amount):
            return None
        transaction.amount = amount
    
    if txn_type is not None:
        if txn_type not in {"income", "outcome"}:
            return None
        transaction.txn_type = txn_type
    
    if transaction_date is not None:
        transaction.transaction_date = transaction_date
    
    db.commit()
    db.refresh(transaction)
    return transaction

def delete_transaction(db: Session, transaction_id: int, user_id: int) -> bool:
    transaction = get_transaction(db, transaction_id, user_id)
    if not transaction:
        return False
    
    db.delete(transaction)
    db.commit()
    return True
    