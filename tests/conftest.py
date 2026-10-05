import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# 仅测试库和假的 R2 凭证；测试不会读取真实 .env 或访问云服务。
os.environ.update({
    'DATABASE_URL': 'sqlite://', 'JWT_SECRET': 'test-login-secret',
    'PLAYBACK_TOKEN_SECRET': 'test-only-secret-32-bytes-0123456789',
    'VIDEO_WORKER_BASE_URL': 'https://media.example.com',
    'R2_ENDPOINT': 'https://r2.example.com', 'R2_ACCESS_KEY_ID': 'test',
    'R2_SECRET_ACCESS_KEY': 'test', 'R2_BUCKET': 'test-bucket',
})
import pytest
from sqlalchemy import create_engine, text, UUID as SQLUUID
from sqlalchemy.ext.compiler import compiles
@compiles(SQLUUID, 'sqlite')
def compile_sqlite_uuid(type_, compiler, **kwargs):
    return 'CHAR(32)' 
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from data_model.core_database import Base, get_db
from data_model.data_model import User, Roles, Account, Systems, Lessons, VideoAsset, SystemLesson
from dependencies.auth import get_current_session
from main import app
from uuid import UUID
from datetime import datetime, timezone

ADMIN = UUID('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
STUDENT = UUID('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb')
ADMIN_USER = UUID('cccccccc-cccc-4ccc-8ccc-cccccccccccc')
STUDENT_USER = UUID('dddddddd-dddd-4ddd-8ddd-dddddddddddd')
ASSET = UUID('11111111-1111-4111-8111-111111111111')
PREFIX = f'videos/hls/{ASSET}/22222222-2222-4222-8222-222222222222/'

@pytest.fixture()
def context(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    # SQLite 只验证查询/授权，PostgreSQL 的默认值和迁移另行验收。
    defaults = []
    for table in Base.metadata.tables.values():
        for column in table.columns:
            defaults.append((column, column.server_default))
            if column.server_default is not None:
                from sqlalchemy import DefaultClause
                if str(column.server_default.arg) == 'now()':
                    column.server_default = DefaultClause(text('CURRENT_TIMESTAMP'))
                elif str(column.server_default.arg) == 'gen_random_uuid()':
                    column.server_default = None
    Base.metadata.create_all(engine)
    for column, default in defaults:
        column.server_default = default
    db = Session(engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)
    db.add_all([Roles(id='admin', role_name='administer'), Roles(id='user', role_name='user')])
    db.add_all([User(id=ADMIN_USER, user_name='Admin', character='engineer'), User(id=STUDENT_USER, user_name='Student', character='operator')])
    db.flush()
    db.add_all([Account(id=ADMIN, user_id=ADMIN_USER, role_id='admin', email='admin@example.com', password='test', is_active=True),
                Account(id=STUDENT, user_id=STUDENT_USER, role_id='user', email='student@example.com', password='test', is_active=True)])
    db.flush()
    db.add(Systems(id=1, system_name='electrical', create_by=ADMIN, created_at=now))
    db.add(VideoAsset(id=ASSET, source_object_key=f'videos/source/{ASSET}.mp4', master_playlist_key=PREFIX+'master.m3u8', status='ready',
                      created_by=ADMIN, created_at=now, updated_at=now, attempt_count=0, declared_size=100, content_type='video/mp4'))
    db.flush()
    db.add(Lessons(id=1, lesson_name='Lesson A', description='description', video_asset_id=ASSET, created_by=ADMIN, created_at=now, update_at=now))
    db.flush()
    db.add(SystemLesson(system_id=1, lesson_id=1)); db.commit()
    identity = {'user_id': str(STUDENT_USER), 'csrf_token': 'test-csrf'}
    def override_db():
        yield db
    async def override_session():
        return identity
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_session] = override_session
    async def no_rate_limit(*args): pass
    monkeypatch.setattr('Router.lessons.lessons.rate_limit', no_rate_limit)
    monkeypatch.setattr('Router.lessons.lesson_video.rate_limit', no_rate_limit)
    with TestClient(app) as client:
        yield client, db, identity
    app.dependency_overrides.clear()
    db.close(); engine.dispose()
