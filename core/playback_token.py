"""与 Worker 共用 HS256 JWT 协议；独立于旧登录 JWT 密钥。"""
import base64
import hashlib
import hmac
import json
import time
from urllib.parse import quote, urlsplit
from uuid import uuid4
from fastapi import HTTPException
from data_model.config import settings


def base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def issue_playback_token(account_id, asset_id, playlist_key: str) -> dict:
    secret = settings.PLAYBACK_TOKEN_SECRET
    base = settings.VIDEO_WORKER_BASE_URL.rstrip("/")
    url = urlsplit(base)
    if len(secret.encode()) < 32 or url.scheme != "https" or not url.netloc or url.path or url.query or url.fragment:
        raise HTTPException(503, "Playback configuration missing")
    prefix = playlist_key.rsplit("/", 1)[0] + "/"
    # 每次转码采用不可变版本目录，令牌只授权该版本的 HLS。
    if not prefix.startswith(f"videos/hls/{asset_id}/") or not playlist_key.endswith("/master.m3u8"):
        raise HTTPException(409, "Invalid HLS asset")
    now = int(time.time())
    ttl = max(120, min(settings.PLAYBACK_TOKEN_TTL, 600))
    payload = {
        "iss": "training-api", "aud": "training-video", "sub": str(account_id),
        "asset": str(asset_id), "prefix": prefix, "iat": now, "exp": now + ttl,
        "jti": str(uuid4()),
    }
    header = base64url(b'{"alg":"HS256","typ":"JWT"}')
    body = base64url(json.dumps(payload, separators=(",", ":")).encode())
    signing = f"{header}.{body}"
    signature = base64url(hmac.new(secret.encode(), signing.encode(), hashlib.sha256).digest())
    token = f"{signing}.{signature}"
    return {
        "play_url": f"{base}/{quote(playlist_key, safe='/')}?token={token}",
        "token": token, "expires_in": ttl, "expires_at": now + ttl,
        "refresh_after": ttl - 60,
    }
