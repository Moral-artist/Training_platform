"""邮箱验证码：五分钟有效、最多五次尝试、原子消费、注册和重置用途隔离。"""

import secrets, hashlib, json
from core.redis_client import redis_client
from uuid import uuid4

OTP_EXPIRE = 300


def hash_code(challenge_id, code):
    return hashlib.sha256(f"{challenge_id}:{code}".encode()).hexdigest()


async def create_email_challenge(
    email, hashed_password, character=None, user_name=None, role_id=None
):
    code = f"{secrets.randbelow(1000000):06d}"
    challenge_id = uuid4().hex
    data = dict(
        email=email,
        user_name=user_name,
        hash_password=hashed_password,
        character=character or "operator",
        role_id=role_id,
        code_hash=hash_code(challenge_id, code),
        attempts=0,
        purpose="register" if role_id else "reset",
    )
    await redis_client.set(
        name=f"email_otp:{challenge_id}", value=json.dumps(data), ex=OTP_EXPIRE
    )
    return challenge_id, code


VERIFY_SCRIPT = """
local raw = redis.call('GET', KEYS[1])
if not raw then return nil end
local data = cjson.decode(raw)
if data.purpose ~= ARGV[2] then return nil end
data.attempts = data.attempts + 1
if data.code_hash ~= ARGV[1] then
  if data.attempts >= 5 then redis.call('DEL', KEYS[1])
  else redis.call('SET', KEYS[1], cjson.encode(data), 'KEEPTTL') end
  return nil
end
redis.call('DEL', KEYS[1])
return raw
"""


async def verify_email_challenge(challenge_id, code, purpose="register"):
    if len(code) != 6 or not code.isdigit() or len(challenge_id) != 32:
        return None
    raw = await redis_client.eval(
        VERIFY_SCRIPT,
        1,
        f"email_otp:{challenge_id}",
        hash_code(challenge_id, code),
        purpose,
    )
    return json.loads(raw) if raw else None
