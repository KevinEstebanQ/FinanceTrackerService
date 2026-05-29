import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from collections.abc import AsyncGenerator
from models.auth_session import AuthSession
from models.user import User
from db.base import Base
from main import app
from httpx import AsyncClient, ASGITransport
from api.deps import get_db
import redis.asyncio as aioredis

MOCK_URL = "postgresql+psycopg_async://test-user:test-password@localhost:5433/test-db"
REDIS_TEST = "redis://localhost:6378/0"
# Fixtures for testing with pytest and async SQLAlchemy sessions
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Creates a test database engine, sets up the schema, and tears it down after tests."""
    engine = create_async_engine(url=MOCK_URL)
    try: 
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    finally:
        await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def test_redis_pool():
    """Provides a Redis client for testing, flushing the database before and after tests."""
    pool = aioredis.ConnectionPool.from_url(REDIS_TEST,
                                            max_connections=50,
                                            decode_responses=True)
    redis = aioredis.Redis(connection_pool=pool)
    await redis.flushdb()
    await redis.aclose()
    yield pool
    

@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provides a new database session for each test, rolling back any changes after the test."""
    async with test_engine.connect() as conn:
        await conn.begin()
        async with AsyncSession(bind=conn, expire_on_commit=False) as session:
            yield session
        await conn.rollback()

@pytest_asyncio.fixture
async def test_client(test_engine, test_session, test_redis_pool) -> AsyncGenerator[AsyncClient, None]:
    """Provides an HTTP client for testing FastAPI endpoints, overriding the database dependency."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app.state.pool = test_redis_pool
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # update async pool fron client
        yield client
    app.dependency_overrides.clear()
    app.state.pool = None





