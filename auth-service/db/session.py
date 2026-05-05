from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.base import Base
from core.config import load_config

config = load_config()

DATABASE_URL = config.get("DATABASE_URL","sqlite:///./auth.db")

if DATABASE_URL.startswith("sqlite"):

    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread":  False}
        ) ##connection to DB
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        ) ##connection to DB

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)##factory for sessions
