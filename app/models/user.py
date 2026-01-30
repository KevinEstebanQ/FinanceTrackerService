from datetime import datetime, UTC
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from app.db.base import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ =  "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable= False)

    auth_sessions = relationship("AuthSession", back_populates="user", cascade="all, delete-orphan")