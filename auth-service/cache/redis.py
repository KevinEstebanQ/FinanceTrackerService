import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool
from models.user import User
from types import SimpleNamespace
from datetime import datetime

async def get_redis(pool: ConnectionPool) -> aioredis.Redis:
    return aioredis.Redis(connection_pool=pool)

async def set_cached_user(redis: aioredis.Redis, user_data: User):
    dump_data = {"id": user_data.id,
      "email": user_data.email,
      "is_active": str(user_data.is_active),
      "created_at": user_data.created_at.isoformat(),}
    
    await redis.hsetex(f"user:{user_data.email}", 
                       mapping=dump_data, ex=300)
    
async def get_cached_user(redis: aioredis.Redis, email: str) -> SimpleNamespace | None:
    user_data = await redis.hgetall(f"user:{email}")
    if not user_data:
        return None
    user_data["is_active"] = user_data["is_active"] == "True"
    user_data["created_at"] = datetime.fromisoformat(user_data["created_at"])
    user_data["id"] = int(user_data["id"])
    return SimpleNamespace(**user_data)