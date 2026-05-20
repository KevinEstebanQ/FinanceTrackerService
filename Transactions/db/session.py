from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .base import Base
from core.config import load_config

config = load_config()

DATABASE_URL = config.get("DATABASE_URL","sqlite:///./finance.db")

if DATABASE_URL.startswith("sqlite"):

    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread":  False}
        ) ##connection to DB
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        ) ##connection to DB

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False,
)##factory for sessions
