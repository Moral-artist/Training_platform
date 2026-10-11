"""Optional real PostgreSQL regressions. Use an isolated TEST_POSTGRES_URL."""

import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from data_model.core_database import Base
from tools.db_setup import migrate


@pytest.fixture
def pg_engine():
    value = os.getenv("TEST_POSTGRES_URL")
    if not value:
        pytest.skip("Set TEST_POSTGRES_URL to an isolated PostgreSQL test database")
    url = make_url(value)
    if url.host not in ("localhost", "127.0.0.1") or url.database != "video_patch_test":
        pytest.fail("Migration tests only allow local database video_patch_test")
    engine = create_engine(url)
    yield engine
    engine.dispose()


def test_legacy_upgrade_preserves_data_and_is_repeatable(pg_engine):
    schema = "video_qa_" + uuid4().hex
    ids = {key: uuid4() for key in ("user", "account")}
    try:
        with pg_engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
            connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}", public')
            connection.exec_driver_sql(
                (Path(__file__).parent / "fixtures/legacy_schema.sql").read_text()
            )
            connection.execute(
                text(
                    "INSERT INTO users(id,user_name,character) VALUES (:user,'legacy','engineer')"
                ),
                ids,
            )
            connection.execute(
                text(
                    "INSERT INTO roles(id,role_name) VALUES ('legacy_role','administer')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO accounts(id,user_id,email,password,role_id,token) VALUES (:account,:user,'legacy@example.com','old-hash','legacy_role','old-token')"
                ),
                ids,
            )
            connection.execute(
                text(
                    "INSERT INTO lessons(id,lesson_name,description,lesson_video_url,created_by) VALUES (1,'old course','old description','https://old.example/video.mp4',:account)"
                ),
                ids,
            )
            # 模拟截图中已有列和 CHECK；迁移应删除它们并保留账号。
            connection.exec_driver_sql(
                "ALTER TABLE accounts ADD COLUMN membership_level varchar(32) NOT NULL DEFAULT 'pro'; "
                "ALTER TABLE accounts ADD CONSTRAINT membership_check "
                "CHECK (membership_level IN ('free','basic','pro'))"
            )
            migrate(connection)
            assert "membership_level" not in {
                c["name"] for c in inspect(connection).get_columns("accounts")
            }
            row = connection.execute(
                text("SELECT is_active,password,token FROM accounts")
            ).one()
            assert row == (True, "old-hash", "old-token")
            assert connection.execute(
                text("SELECT lesson_video_url,video_asset_id FROM lessons")
            ).one() == ("https://old.example/video.mp4", None)
            asset_columns = {
                c["name"] for c in inspect(connection).get_columns("video_assets")
            }
            assert {
                "duration_seconds",
                "processing_started_at",
                "declared_size",
                "attempt_count",
            } <= asset_columns
            migrate(connection)
            assert "membership_level" not in {
                c["name"] for c in inspect(connection).get_columns("accounts")
            }
            assert (
                connection.execute(text("SELECT count(*) FROM lessons")).scalar_one()
                == 1
            )
            assert (
                connection.execute(text("SELECT count(*) FROM accounts")).scalar_one()
                == 1
            )
    finally:
        with pg_engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


def test_missing_video_tables_are_created(pg_engine):
    schema = "video_qa_" + uuid4().hex
    try:
        with pg_engine.begin() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
            connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}", public')
            connection.exec_driver_sql(
                (Path(__file__).parent / "fixtures/legacy_schema.sql").read_text()
            )
            connection.exec_driver_sql(
                "DROP TABLE lesson_access; DROP TABLE video_assets"
            )
            migrate(connection)
            assert inspect(connection).has_table("video_assets")
            assert inspect(connection).has_table("lesson_access")
    finally:
        with pg_engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


def test_duplicate_accounts_abort_upgrade_without_partial_changes(pg_engine):
    schema = "video_qa_" + uuid4().hex
    try:
        with pg_engine.begin() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
            connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}", public')
            connection.exec_driver_sql(
                (Path(__file__).parent / "fixtures/legacy_schema.sql").read_text()
            )
            connection.exec_driver_sql(
                "INSERT INTO users(user_name,character) VALUES ('legacy','engineer'); INSERT INTO roles(id,role_name) VALUES ('r','user')"
            )
            connection.exec_driver_sql(
                "INSERT INTO accounts(user_id,email,password,role_id,token) SELECT id,'a@example.com','hash','r','token' FROM users; INSERT INTO accounts(user_id,email,password,role_id,token) SELECT id,'b@example.com','hash','r','token' FROM users"
            )
        with pytest.raises(Exception):
            with pg_engine.begin() as connection:
                connection.exec_driver_sql(
                    f'SET LOCAL search_path TO "{schema}", public'
                )
                migrate(connection)
        with pg_engine.connect() as connection:
            connection.exec_driver_sql(f'SET search_path TO "{schema}", public')
            assert "is_active" not in {
                c["name"] for c in inspect(connection).get_columns("accounts")
            }
            assert (
                connection.execute(text("SELECT count(*) FROM accounts")).scalar_one()
                == 2
            )
    finally:
        with pg_engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


def test_new_schema_already_accepts_upgrade(pg_engine):
    schema = "video_qa_" + uuid4().hex
    try:
        with pg_engine.begin() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
            connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}", public')
            Base.metadata.create_all(connection)
            migrate(connection)
            assert inspect(connection).has_table("lesson_access")
    finally:
        with pg_engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
