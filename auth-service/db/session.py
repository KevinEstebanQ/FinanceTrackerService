from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from db.base import Base
from core.config import load_config

config = load_config()

DATABASE_URL = config.get("DATABASE_URL","sqlite:///./auth.db")

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
    engine, expire_on_commit=False,
)##factory for sessions
