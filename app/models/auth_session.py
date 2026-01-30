from app.db.base import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime,UTC


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,ForeignKey("users.id"), unique=False , nullable=False)
    token_hash = Column(String(255),nullable=False, index=True, unique=True)
    expires_at = Column(DateTime, unique=False, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda:datetime.now(UTC))
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    ip  = Column(String(45), nullable=True)