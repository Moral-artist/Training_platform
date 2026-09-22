import secrets
from core.redis_client import redis_client
import json

SESSION_TTL = 7 * 24 * 60 * 60

async def create_session(user_id:str):
    session_id = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)

    session_data = {
        "user_id": user_id,
        "csrf_token": csrf_token,
    }

    await redis_client.set(
        name=f"session:{session_id}",
        value=json.dumps(session_data),
        ex=SESSION_TTL
    )
    return session_id, csrf_token

async def get_session(session_id):
    session_data = await redis_client.get(f"session:{session_id}")

    if session_data is None:
        return None
    return json.loads(session_data)

async def delete_session(session_id):
    await redis_client.delete(f"session:{session_id}")