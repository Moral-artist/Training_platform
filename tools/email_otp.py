import secrets
import hashlib
import hmac
import json
from core.redis_client import redis_client
from uuid import uuid4

OTP_EXPIRE = 300

def hash_code(challenge_id:str, code:str):
    data = f"{challenge_id}:{code}"
    return hashlib.sha256(
        data.encode("utf-8")
    ).hexdigest()

async def create_email_challenge(
        email:str,
        hashed_password:str,
        character: str,
        user_name:str = None,
        role_id:str = None,
):
    code = f"{secrets.randbelow(100000):06d}"

    challenge_id = uuid4().hex

    data = {
        "email": email,
        "user_name": user_name,
        "hash_password": hashed_password,
        "character": character,
        "role_id": role_id,
        "code_hash": hash_code(challenge_id, code),
        "attempts":0
    }

    await redis_client.set(
        name=f"email_otp:{challenge_id}",
        value=json.dumps(data),
        ex=OTP_EXPIRE,
    )

    return challenge_id, code

async def verify_email_challenge(challenge_id:str, code:str):
    key=f"email_otp:{challenge_id}"
    raw_data = await redis_client.get(key)
    if raw_data is None:
        return None
    submitted_code = hash_code(challenge_id, code)
    data = json.loads(raw_data)
    if not hmac.compare_digest(submitted_code, data["code_hash"]):
        return None
    return data
