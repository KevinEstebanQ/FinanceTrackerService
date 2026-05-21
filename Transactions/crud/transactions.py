from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Select, update,Delete
from models.transactions import Transaction
from schemas.transaction import TransactionSingle,TransactionGet
from datetime import datetime
from typing import List
import math
from cache.redis import get_cached_transactions, set_cached_txn, get_redis

async def create_new_transaction(db: AsyncSession, desc: str, amount: float, txn_type: str, transaction_date: datetime, user_id: int) -> Transaction | None:
    if txn_type not in {"income", "outcome"}:
        return None
    if not desc:
        return None
    if amount is None or amount <= 0 or math.isinf(amount):
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
    await db.commit()
    await db.refresh(new_transaction)
    return new_transaction


async def get_user_transactions(db: AsyncSession, user_id: int, limit: int = 10) -> TransactionGet:
    stmt = Select(Transaction).where(Transaction.user_id == user_id).limit(limit)
    transaction = await db.execute(stmt)
    transaction = transaction.scalars().all()
    return [TransactionSingle(amount=txn.amount, txn_type=txn.txn_type, desc=txn.desc, transaction_date=txn.transaction_date) for txn in transaction]