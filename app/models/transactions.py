from app.db.base import Base
from sqlalchemy import Numeric, Column, DateTime, Integer, String, REAL, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, index=True, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=False, nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    created_at = Column(DateTime, default= lambda: datetime.utcnow())
    txn_type = Column(String, nullable=False)
    desc = Column(String, nullable=False)
    transaction_date = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="transactions")

