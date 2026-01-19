from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import dotenv_values

from app.db.base import Base

config = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env")
}

DATABASE_URL = config.get("DATABASE_URL","sqlite:///./finance.db")

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