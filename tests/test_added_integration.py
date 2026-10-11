import asyncio
from pathlib import Path
import shutil
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from conftest import ADMIN, ADMIN_USER, ASSET, STUDENT, STUDENT_USER
from data_model.data_model import Account, LessonAccess, VideoAsset
from data_model.config import settings
from tools import transcode_worker as worker

CSRF = {"X-CSRF-Token": "test-csrf"}


def test_all_lessons_hides_ungranted_metadata(context):
    client, db, identity = context
    assert client.get("/api/lessons/alllessons").json() == []
    db.add(LessonAccess(account_id=STUDENT, lesson_id=1, granted_by=ADMIN))
    db.commit()
    assert (
        client.get("/api/lessons/alllessons").json()[0]["lessons"][0]["lesson_id"] == 1
    )
    identity["user_id"] = str(ADMIN_USER)
    assert client.get("/api/lessons/alllessons").status_code == 200


def test_login_rejects_disabled_accounts(context):
    client, db, _ = context
    account = db.get(Account, STUDENT)
    account.is_active = False
    db.commit()
    assert (
        client.post(
            "/api/auth/login", json={"email": "student@example.com", "password": "test"}
        ).status_code
        == 403
    )


def test_get_user_info_and_my_lessons_do_not_require_csrf(context):
    client, _, _ = context
    response = client.get("/api/user/user_info")
    assert response.status_code == 200 and response.json()["role"] == "user"
    assert response.json()["csrf_token"] == "test-csrf"
    assert client.get("/api/user/my_lessons").status_code == 200


def test_registration_confirmation_without_membership(context, monkeypatch):
    from Router.auth import auth as auth_router
    from data_model.data_model import User

    client, db, _ = context

    async def verified(challenge_id, code):
        return {
            "user_name": "Registered",
            "character": "operator",
            "email": "registered@example.com",
            "hash_password": "test-hash",
            "role_id": "user",
        }

    monkeypatch.setattr(auth_router, "verify_email_challenge", verified)
    # SQLite 没有 PostgreSQL 的 UUID 默认函数，为测试中的新对象提供 ID。
    monkeypatch.setattr(
        auth_router, "User", lambda **fields: User(id=uuid4(), **fields)
    )
    monkeypatch.setattr(
        auth_router, "Account", lambda **fields: Account(id=uuid4(), **fields)
    )
    response = client.post(
        "/api/auth/verify_register", params={"code": "123456", "challenge_id": "test"}
    )
    assert response.status_code == 200
    account = db.query(Account).filter_by(email="registered@example.com").one()
    assert account.role_id == "user" and account.is_active is True


def test_missing_playback_settings_is_service_error(context, monkeypatch):
    client, db, _ = context
    db.add(LessonAccess(account_id=STUDENT, lesson_id=1, granted_by=ADMIN))
    db.commit()
    monkeypatch.setattr(settings, "PLAYBACK_TOKEN_SECRET", "")
    assert client.post("/api/lessons/1/play", headers=CSRF).status_code == 503


def test_playback_rate_limit_enforced_without_issuing_more_tokens(context, monkeypatch):
    from Router.lessons import lessons
    from service import video_limits

    client, db, _ = context
    db.add(LessonAccess(account_id=STUDENT, lesson_id=1, granted_by=ADMIN))
    db.commit()
    calls = {}

    async def eval_counter(script, count, key, seconds):
        calls[key] = calls.get(key, 0) + 1
        assert seconds == 600
        return calls[key]

    monkeypatch.setattr(video_limits.redis_client, "eval", eval_counter)
    monkeypatch.setattr(lessons, "rate_limit", video_limits.rate_limit)
    for _ in range(60):
        assert client.post("/api/lessons/1/play", headers=CSRF).status_code == 200
    response = client.post("/api/lessons/1/play", headers=CSRF)
    assert response.status_code == 429 and response.headers["Retry-After"] == "600"
    assert "token" not in response.json()


def test_real_ffmpeg_queue_to_signed_playback(context, monkeypatch, tmp_path):
    """Real FFmpeg + database queue + fake R2 storage + actual HTTP playback endpoint."""
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("Install FFmpeg/FFprobe to run real media conversion")
    client, db, _ = context
    monkeypatch.setattr(settings, "FFMPEG_PATH", shutil.which("ffmpeg"))
    monkeypatch.setattr(settings, "FFPROBE_PATH", shutil.which("ffprobe"))
    source = tmp_path / "source.mp4"
    subprocess.run(
        [
            settings.FFMPEG_PATH,
            "-nostdin",
            "-y",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=640x360:rate=10",
            "-t",
            "2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
        timeout=30,
    )
    contents = source.read_bytes()
    asset = db.get(VideoAsset, ASSET)
    asset.status = "uploaded"
    db.add(LessonAccess(account_id=STUDENT, lesson_id=1, granted_by=ADMIN))
    db.commit()
    monkeypatch.setattr(
        worker, "SessionLocal", lambda: Session(db.bind, expire_on_commit=False)
    )
    monkeypatch.setattr(
        worker.r2, "head_object", lambda **kwargs: {"ContentLength": len(contents)}
    )
    monkeypatch.setattr(
        worker.r2,
        "download_file",
        lambda bucket, key, filename: Path(filename).write_bytes(contents),
    )
    objects = {}

    def upload(filename, bucket, key, **kwargs):
        objects[key] = Path(filename).read_bytes()

    monkeypatch.setattr(worker.r2, "upload_file", upload)
    worker.process_asset(worker.claim_asset())
    db.expire_all()
    asset = db.get(VideoAsset, ASSET)
    assert asset.status == "ready" and asset.duration_seconds > 0
    assert objects[asset.master_playlist_key].startswith(b"#EXTM3U")
    assert any(key.endswith(".ts") and contents for key, contents in objects.items())
    playback = client.post("/api/lessons/1/play", headers=CSRF)
    assert (
        playback.status_code == 200
        and "master.m3u8?token=" in playback.json()["play_url"]
    )
