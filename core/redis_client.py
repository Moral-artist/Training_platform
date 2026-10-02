import redis.asyncio as redis
from data_model.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
