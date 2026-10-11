"""权限边界、上传恢复与幂等、课程并发编辑、计划、考试回归。外部存储全部使用替身。"""

from datetime import datetime, timezone
from uuid import uuid4, UUID
import pytest
from botocore.exceptions import ClientError
from sqlalchemy import select
from data_model.data_model import (
    Account,
    Roles,
    Systems,
    VideoAsset,
    Lessons,
    LessonAccess,
)
from main import app
from tools.permission_auth import optional_account, resolve_account
from conftest import ADMIN, ADMIN_USER, STUDENT, STUDENT_USER, ASSET

CSRF = {"X-CSRF-Token": "test-csrf"}


def as_admin(identity):
    identity["user_id"] = str(ADMIN_USER)


def expose_identity(db, identity):
    def optional():
        return resolve_account(db, identity)

    app.dependency_overrides[optional_account] = optional


def test_public_catalog_lists_all_systems_without_private_data(context):
    client, db, identity = context
    db.add(Systems(id=2, system_name="new-specialty", create_by=ADMIN))
    db.commit()
    result = client.get("/api/lessons/catalog")
    assert result.status_code == 200
    assert len(result.json()) == 2 and result.json()[1]["lessons"] == []
    lesson = result.json()[0]["lessons"][0]
    assert lesson["can_access"] is False and lesson["access_reason"] == "login_required"
    assert set(lesson) == {
        "lesson_id",
        "lesson_name",
        "video_status",
        "can_access",
        "access_reason",
    }
    assert (
        "description" not in result.text
        and "videos/" not in result.text
        and "token" not in result.text
    )


def test_logged_in_catalog_flags_grants_without_hiding_other_courses(context):
    client, db, identity = context
    expose_identity(db, identity)
    assert (
        client.get("/api/lessons/catalog").json()[0]["lessons"][0]["access_reason"]
        == "grant_required"
    )
    db.add(LessonAccess(account_id=STUDENT, lesson_id=1, granted_by=ADMIN))
    db.commit()
    assert (
        client.get("/api/lessons/catalog").json()[0]["lessons"][0]["can_access"] is True
    )


def test_profile_returns_context_and_cannot_elevate_role(context):
    client, db, identity = context
    data = client.get("/api/user/user_info").json()
    assert data["account_id"] == str(STUDENT) and data["character"] == "operator"
    assert "membership_level" not in data
    response = client.post(
        "/api/user/edit_profile",
        json={"username": "New Name", "character": "engineer", "role": "administer"},
        headers=CSRF,
    )
    assert response.status_code == 200
    assert client.get("/api/user/user_info").json()["role"] == "user"
    assert (
        client.post(
            "/api/user/edit_profile",
            json={"username": "   ", "character": "engineer"},
            headers=CSRF,
        ).status_code
        == 422
    )
    db.get(Account, STUDENT).is_active = False
    db.commit()
    assert client.get("/api/user/user_info").status_code == 403
    assert (
        client.post(
            "/api/user/edit_profile",
            json={"username": "No", "character": "operator"},
            headers=CSRF,
        ).status_code
        == 403
    )


def course_body():
    return {
        "system_id": 1,
        "lesson_name": "A new lesson",
        "description": "description",
        "video_asset_id": str(ASSET),
        "request_id": str(uuid4()),
    }


def test_create_idempotent_with_payload_conflict_detection(context):
    client, db, identity = context
    as_admin(identity)
    body = course_body()
    first = client.post("/api/lessons/lessonsubmit", json=body, headers=CSRF)
    second = client.post("/api/lessons/lessonsubmit", json=body, headers=CSRF)
    assert (
        first.status_code == second.status_code == 200
        and first.json()["lesson_id"] == second.json()["lesson_id"]
    )
    assert (
        client.post(
            "/api/lessons/lessonsubmit",
            json={**body, "lesson_name": "different"},
            headers=CSRF,
        ).status_code
        == 409
    )
    assert len(db.scalars(select(Lessons)).all()) == 2


def test_manager_owns_asset_can_create_edit_and_read(context):
    client, db, identity = context
    db.add(Roles(id="manager", role_name="manager"))
    db.get(Account, STUDENT).role_id = "manager"
    db.get(VideoAsset, ASSET).created_by = STUDENT
    db.commit()
    result = client.post("/api/lessons/lessonsubmit", json=course_body(), headers=CSRF)
    assert result.status_code == 200
    lesson = client.get(f"/api/lessons/{result.json()['lesson_id']}/detail").json()
    assert lesson["can_manage"] is True
    update = {
        "system_id": 1,
        "lesson_name": "Edited",
        "description": "new",
        "video_asset_id": str(ASSET),
        "revision": 1,
    }
    assert (
        client.put(
            f"/api/lessons/{lesson['lesson_id']}", json=update, headers=CSRF
        ).status_code
        == 200
    )
    # 上传者也可以修改管理员创建的课程。
    assert client.get("/api/lessons/1/detail").json()["can_manage"] is True


def test_manager_cannot_bind_another_uploaders_asset(context):
    client, db, _ = context
    db.add(Roles(id="manager", role_name="manager"))
    db.get(Account, STUDENT).role_id = "manager"
    db.commit()
    assert (
        client.post(
            "/api/lessons/lessonsubmit", json=course_body(), headers=CSRF
        ).status_code
        == 403
    )


def test_course_edit_version_and_delete_permissions(context):
    client, db, identity = context
    body = {
        "system_id": 1,
        "lesson_name": "Edited",
        "description": "new",
        "video_asset_id": str(ASSET),
        "revision": 1,
    }
    assert client.put("/api/lessons/1", json=body, headers=CSRF).status_code == 403
    assert client.delete("/api/lessons/1?revision=1", headers=CSRF).status_code == 403
    as_admin(identity)
    assert client.put("/api/lessons/1", json=body, headers=CSRF).json()["revision"] == 2
    assert client.put("/api/lessons/1", json=body, headers=CSRF).status_code == 409
    assert client.delete("/api/lessons/1?revision=1", headers=CSRF).status_code == 409
    assert client.delete("/api/lessons/1?revision=2", headers=CSRF).status_code == 200
    assert client.get("/api/lessons/1/detail").status_code == 404
    assert client.post("/api/lessons/1/play", headers=CSRF).status_code == 404
    assert client.get("/api/lessons/catalog").json()[0]["lessons"] == []
    assert db.get(Lessons, 1) is not None


class FakeMultipart:
    def __init__(self):
        self.parts = {}
        self.objects = {}
        self.created = 0
        self.aborted = []

    def create_multipart_upload(self, **kwargs):
        self.created += 1
        self.key = kwargs["Key"]
        self.type = kwargs["ContentType"]
        return {"UploadId": "upload-1"}

    def list_parts(self, **kwargs):
        return {
            "Parts": [
                {"PartNumber": n, "Size": s, "ETag": f"part-{n}"}
                for n, s in sorted(self.parts.items())
            ]
        }

    def generate_presigned_url(self, *args, **kwargs):
        return "https://r2.example.com/part"

    def head_object(self, **kwargs):
        if kwargs["Key"] not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        return self.objects[kwargs["Key"]]

    def complete_multipart_upload(self, **kwargs):
        self.objects[kwargs["Key"]] = {
            "ContentLength": sum(self.parts.values()),
            "ContentType": self.type,
        }

    def abort_multipart_upload(self, **kwargs):
        self.aborted.append(kwargs["UploadId"])

    def delete_object(self, **kwargs):
        self.objects.pop(kwargs["Key"], None)


@pytest.fixture
def multipart(monkeypatch):
    from Router.lessons import uploads

    fake = FakeMultipart()
    monkeypatch.setattr(uploads, "r2", fake)

    async def no_rate(*args):
        pass

    monkeypatch.setattr(uploads, "rate_limit", no_rate)
    return fake


def upload_body():
    return {
        "filename": "large.mp4",
        "size": 20 * 1024 * 1024,
        "content_type": "video/mp4",
        "content_hash": "a" * 64,
    }


def test_multipart_resume_dedup_and_complete_idempotent(context, multipart):
    client, db, identity = context
    as_admin(identity)
    body = upload_body()
    first = client.post("/api/uploads/start", json=body, headers=CSRF)
    assert first.status_code == 200
    aid = first.json()["asset_id"]
    assert "upload_id" not in first.text and "videos/" not in first.text
    assert (
        client.post("/api/uploads/start", json=body, headers=CSRF).json()["asset_id"]
        == aid
        and multipart.created == 1
    )
    multipart.parts = {1: 16 * 1024 * 1024}
    assert client.get(f"/api/uploads/{aid}").json()["parts"] == [
        {"part_number": 1, "size": 16 * 1024 * 1024}
    ]
    assert (
        client.post(f"/api/uploads/{aid}/part?part_number=2", headers=CSRF).status_code
        == 200
    )
    assert (
        client.post(f"/api/uploads/{aid}/part?part_number=3", headers=CSRF).status_code
        == 422
    )
    assert client.post(f"/api/uploads/{aid}/complete", headers=CSRF).status_code == 409
    multipart.parts[2] = 4 * 1024 * 1024
    for _ in range(2):
        assert (
            client.post(f"/api/uploads/{aid}/complete", headers=CSRF).json()["status"]
            == "uploaded"
        )
    assert client.delete(f"/api/uploads/{aid}", headers=CSRF).status_code == 409


def test_multipart_server_crash_after_r2_complete_recovers(context, multipart):
    client, db, identity = context
    as_admin(identity)
    body = upload_body()
    aid = client.post("/api/uploads/start", json=body, headers=CSRF).json()["asset_id"]
    multipart.objects[multipart.key] = {
        "ContentLength": body["size"],
        "ContentType": body["content_type"],
    }
    assert (
        client.post(f"/api/uploads/{aid}/complete", headers=CSRF).json()["status"]
        == "uploaded"
    )


def test_multipart_rejects_ownership_mismatch_and_allows_discard(context, multipart):
    client, db, identity = context
    as_admin(identity)
    aid = client.post("/api/uploads/start", json=upload_body(), headers=CSRF).json()[
        "asset_id"
    ]
    identity["user_id"] = str(STUDENT_USER)
    assert client.get(f"/api/uploads/{aid}").status_code == 403
    assert (
        client.post(f"/api/uploads/{aid}/part?part_number=1", headers=CSRF).status_code
        == 403
    )
    assert client.delete(f"/api/uploads/{aid}", headers=CSRF).status_code == 403
    as_admin(identity)
    assert client.delete(f"/api/uploads/{aid}", headers=CSRF).status_code == 200
    assert multipart.aborted == ["upload-1"]
    assert db.get(VideoAsset, UUID(aid)) is None


def test_multipart_rejects_bad_size_and_content(context, multipart):
    client, db, identity = context
    as_admin(identity)
    body = upload_body()
    assert (
        client.post(
            "/api/uploads/start", json={**body, "size": 9 * 1024**3}, headers=CSRF
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/uploads/start", json={**body, "content_hash": "x"}, headers=CSRF
        ).status_code
        == 422
    )
    aid = client.post("/api/uploads/start", json=body, headers=CSRF).json()["asset_id"]
    multipart.parts = {1: 15 * 1024 * 1024, 2: 5 * 1024 * 1024}
    assert client.post(f"/api/uploads/{aid}/complete", headers=CSRF).status_code == 422


def test_plan_requires_permission_and_tracks_completion(context):
    client, db, identity = context
    body = {"plan_name": "mine", "lesson_list": [{"lesson_id": 1, "order": 1}]}
    assert (
        client.post("/api/plan/add_custom_plan", json=body, headers=CSRF).status_code
        == 403
    )
    db.add(LessonAccess(account_id=STUDENT, lesson_id=1, granted_by=ADMIN))
    db.commit()
    result = client.post("/api/plan/add_custom_plan", json=body, headers=CSRF)
    assert result.status_code == 200
    pid = result.json()["plan_id"]
    assert (
        client.put(
            f"/api/plan/{pid}/lessons/1/progress",
            json={"completed": True},
            headers=CSRF,
        ).json()["status"]
        == "completed"
    )
    assert client.get("/api/plan/mine").json()[0]["lessons"][0]["completed"] is True
    as_admin(identity)
    assert (
        client.put(
            f"/api/plan/{pid}/lessons/1/progress",
            json={"completed": False},
            headers=CSRF,
        ).status_code
        == 404
    )


def exam_body():
    return {
        "exam_name": "Test",
        "lesson_id": 1,
        "questions": [
            {
                "question_name": "A or B?",
                "question_type": "singleQuestion",
                "options": [
                    {"option_key": "A", "option_value": "yes", "is_correct": True},
                    {"option_key": "B", "option_value": "no", "is_correct": False},
                ],
            }
        ],
    }


def test_exam_course_permission_grading_and_refresh(context):
    client, db, identity = context
    as_admin(identity)
    eid = client.post("/api/exams/createExams", json=exam_body(), headers=CSRF).json()[
        "exam_id"
    ]
    identity["user_id"] = str(STUDENT_USER)
    assert client.get("/api/exams/getExams?lesson_id=1").status_code == 403
    assert (
        client.post(
            "/api/exams/attemptExam",
            json={"lesson_id": 1, "exam_id": eid},
            headers=CSRF,
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/exams/createExams", json=exam_body(), headers=CSRF
        ).status_code
        == 403
    )
    db.add(LessonAccess(account_id=STUDENT, lesson_id=1, granted_by=ADMIN))
    db.commit()
    # 无会员等级，课程授权后即可读取考试。
    assert client.get("/api/exams/getExams?lesson_id=1").status_code == 200
    exam = client.get("/api/exams/getExams?lesson_id=1").json()[0]
    assert "is_correct" not in str(exam) and "answer" not in exam["questions"][0]
    body = {"lesson_id": 1, "exam_id": eid}
    aid = client.post("/api/exams/attemptExam", json=body, headers=CSRF).json()[
        "attempt_id"
    ]
    assert (
        client.post("/api/exams/attemptExam", json=body, headers=CSRF).json()[
            "attempt_id"
        ]
        == aid
    )
    submit = {
        "attempt_id": aid,
        "questions": [{"q_id": exam["questions"][0]["question_id"], "answer": "A"}],
    }
    # 移除等级校验后，交卷仍必须检查当前课程授权。
    grant = db.get(LessonAccess, (STUDENT, 1))
    db.delete(grant)
    db.commit()
    assert (
        client.post("/api/exams/submitAttempt", json=submit, headers=CSRF).status_code
        == 403
    )
    db.add(LessonAccess(account_id=STUDENT, lesson_id=1, granted_by=ADMIN))
    db.commit()
    first = client.post("/api/exams/submitAttempt", json=submit, headers=CSRF)
    assert first.status_code == 200 and first.json()["score"] == 100
    assert (
        client.post("/api/exams/submitAttempt", json=submit, headers=CSRF).json()[
            "score"
        ]
        == 100
    )
    assert client.get("/api/exams/my_attempts").json()[0]["submitted"] is True
    assert (
        client.post(
            "/api/exams/attemptExam", json={**body, "exam_id": 999}, headers=CSRF
        ).status_code
        == 404
    )


def test_admin_account_changes_guard_self_demotion(context):
    client, db, identity = context
    assert client.get("/api/admin/accounts").status_code == 403
    as_admin(identity)
    body = {"role": "user", "is_active": True}
    assert (
        client.put(
            f"/api/admin/accounts/{STUDENT}", json=body, headers=CSRF
        ).status_code
        == 200
    )
    assert db.get(Account, STUDENT).role_id == "user"
    assert (
        client.put(f"/api/admin/accounts/{ADMIN}", json=body, headers=CSRF).status_code
        == 409
    )
    response = client.get("/api/admin/accounts")
    assert "password" not in response.text and "token" not in response.text
    assert "membership_level" not in response.text


def test_transcode_levels_respect_source_and_requested_4k(monkeypatch):
    from tools.transcode_worker import select_levels
    from data_model.config import settings

    monkeypatch.setattr(settings, "HLS_HEIGHTS", "720,1080,1440,2160")
    assert select_levels(2160, 3840) == [720, 1080, 1440, 2160]
    assert select_levels(720, 1280) == [720]
    assert select_levels(480, 640) == [480]
    assert select_levels(3840, 2160) == [720, 1080, 1440, 2160]


def test_password_reset_invalidates_every_old_session(context, monkeypatch):
    import asyncio
    from dependencies import auth as session_auth
    from Router.auth import auth as auth_router
    from core.security import hash_password
    from fastapi import HTTPException

    client, db, identity = context

    async def stored_session(session_id):
        return {
            "user_id": str(STUDENT_USER),
            "csrf_token": "old-csrf",
            "auth_version": 0,
        }

    monkeypatch.setattr(session_auth, "get_session", stored_session)
    assert (
        asyncio.run(session_auth.get_current_session("old-session", db))["auth_version"]
        == 0
    )

    async def verified(challenge_id, code, purpose):
        assert purpose == "reset"
        return {
            "email": "student@example.com",
            "hash_password": hash_password("A-new-password-123!"),
        }

    monkeypatch.setattr(auth_router, "verify_email_challenge", verified)
    assert (
        client.post("/api/auth/verify_reset?challenge_id=test&code=123456").status_code
        == 200
    )
    db.expire_all()
    assert db.get(Account, STUDENT).auth_version == 1
    with pytest.raises(HTTPException) as error:
        asyncio.run(session_auth.get_current_session("another-old-session", db))
    assert error.value.status_code == 401
