from fastapi import HTTPException
from core.redis_client import redis_client

# 原子递增和设置到期；不会留下永不过期的限流键。
RATE_SCRIPT = """
local n = redis.call('INCR', KEYS[1])
if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return n
"""

async def rate_limit(account_id, action: str, limit: int, seconds: int):
    count = await redis_client.eval(RATE_SCRIPT, 1, f"video-limit:{action}:{account_id}", seconds)
    if count > limit:
        raise HTTPException(429, "Too many video requests", headers={"Retry-After": str(seconds)})
