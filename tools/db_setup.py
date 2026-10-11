"""Explicit PostgreSQL setup; check-only unless --apply is supplied."""

import argparse
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from data_model.config import settings
from data_model.core_database import Base
import data_model.data_model  # register every table

ROOT = Path(__file__).resolve().parents[1]


def migrate(connection):
    inspector = inspect(connection)
    required = {
        "accounts": {"id", "user_id", "email", "password", "role_id", "token"},
        "lessons": {"id", "lesson_video_url", "created_by"},
        "users": {"id"},
        "roles": {"id"},
    }
    if "video_assets" in inspector.get_table_names():
        required["video_assets"] = {
            "id",
            "source_object_key",
            "master_playlist_key",
            "status",
            "error_message",
            "created_by",
            "created_at",
            "updated_at",
        }
    if "lesson_access" in inspector.get_table_names():
        required["lesson_access"] = {
            "account_id",
            "lesson_id",
            "granted_by",
            "created_at",
        }
    for table, names in required.items():
        if not inspector.has_table(table):
            raise ValueError(
                f"Missing base table {table}; use init for an empty database"
            )
        actual = {column["name"] for column in inspector.get_columns(table)}
        if names - actual:
            raise ValueError(
                f"Schema mismatch in {table}: missing {sorted(names - actual)}"
            )
    connection.exec_driver_sql((ROOT / "migrations/001_video_upgrade.sql").read_text())
    connection.exec_driver_sql(
        (ROOT / "migrations/002_platform_upgrade.sql").read_text()
    )
    # 在同一事务中移除旧等级列；失败时回滚整个升级。
    connection.exec_driver_sql(
        (ROOT / "migrations/003_remove_membership.sql").read_text()
    )
    # 原备份可能缺少考试表；只创建缺失表，不重建或清空已有业务数据。
    Base.metadata.create_all(connection)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("init", "migrate"))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply to DATABASE_URL; default only prints target",
    )
    args = parser.parse_args()
    url = make_url(settings.DATABASE_URL)
    if url.get_backend_name() != "postgresql":
        parser.error("This setup tool requires PostgreSQL")
    print(f"Target: host={url.host}, port={url.port or 5432}, database={url.database}")
    if not args.apply:
        print(
            "Check-only: no changes. init creates an empty DB schema; migrate upgrades existing tables."
        )
        if args.action == "migrate":
            print(
                "This version removes accounts.membership_level and its stored values."
            )
        print("Confirm the target and back up any existing database, then add --apply.")
        return
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            if args.action == "init":
                if inspect(connection).get_table_names():
                    raise ValueError(
                        "Database already has tables; init will not overwrite them"
                    )
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
                Base.metadata.create_all(connection)
            else:
                migrate(connection)
        print(
            f"{args.action} completed; no account passwords or Cloudflare credentials were changed."
        )
    except Exception as error:
        # Driver exception text may contain connection credentials. Emit only the class.
        if isinstance(error, ValueError):
            print(str(error))
        else:
            print(
                f"Database operation failed ({type(error).__name__}); transaction rolled back."
            )
        raise SystemExit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
