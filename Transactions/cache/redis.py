import redis.asyncio as aioredis
from types import SimpleNamespace
from schemas.transaction import TransactionGet, TransactionSingle
import json

async def get_redis(pool: aioredis.ConnectionPool)-> aioredis.Redis:
    return aioredis.Redis(connection_pool=pool)

async def set_cached_user(redis: aioredis.Redis, user_data: SimpleNamespace):
    data_mapping = {"user_id":user_data.user_id,
                            "email":user_data.email}
    await redis.hsetex(name=f"email: {user_data.email}", 
                       mapping=data_mapping, ex=300)

async def get_cached_user(redis: aioredis.Redis, email: str)-> SimpleNamespace | None:
    cached_data = await redis.hgetall(f"email: {email}")
    if not cached_data:
        return None
    return SimpleNamespace(user_id=int(cached_data["user_id"]), email=cached_data["email"])
    
async def set_cached_txn(redis:aioredis.Redis, txn_data:TransactionGet, user_id: int):
    dumped_model = [t.model_dump(mode="json") for t in txn_data.transactions]
    json_dumped_data = json.dumps(dumped_model)

    await redis.hsetex(name=f"transactions_{user_id}", 
                       mapping={"txns":json_dumped_data},
                       ex=30)

async def get_cached_transactions(redis: aioredis.Redis, user_id) -> TransactionGet | None:
    cached_transactions_obj = await redis.hgetall(f"transactions_{user_id}")
    if not cached_transactions_obj:
        return None
    return TransactionGet(transactions=json.loads(cached_transactions_obj["txns"]))