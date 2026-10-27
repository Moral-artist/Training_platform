"""Manually rebuild an empty PostgreSQL schema from the current data model.

The application and transcode worker never import this module. Production Docker
builds exclude it, so database recovery cannot run as part of service startup.
"""

from __future__ import annotations

import argparse

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from data_model.config import settings
from data_model.core_database import Base
import data_model.data_model  # noqa: F401 - register every mapped table


CONFIRMATION_TEXT = "RESTORE_EMPTY_DATABASE"
PRODUCTION_ENVIRONMENTS = {"prod", "production"}


def expected_table_names() -> set[str]:
    """Return the tables defined by the current data model."""

    return set(Base.metadata.tables)


def require_safe_request(
    *,
    apply: bool,
    confirmation: str | None,
    environment: str,
    allow_production_recovery: bool,
) -> None:
    """Reject implicit execution and unapproved production recovery."""

    if not apply:
        return
    if confirmation != CONFIRMATION_TEXT:
        raise ValueError(
            f"Recovery requires --confirm {CONFIRMATION_TEXT}; no changes were made"
        )
    if (
        environment.strip().lower() in PRODUCTION_ENVIRONMENTS
        and not allow_production_recovery
    ):
        raise ValueError(
            "Production recovery is blocked. Run from an administrator checkout "
            "and add --allow-production-recovery after confirming the target and backup"
        )


def require_empty_database(existing_tables: set[str]) -> None:
    """Never modify, migrate, truncate, or merge an existing database."""

    if existing_tables:
        names = ", ".join(sorted(existing_tables))
        raise ValueError(
            f"Target database is not empty ({names}); no changes were made"
        )


def restore_empty_database(connection) -> list[str]:
    """Create the current model schema in an empty PostgreSQL database."""

    existing = set(inspect(connection).get_table_names(schema="public"))
    require_empty_database(existing)

    connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    Base.metadata.create_all(connection, checkfirst=False)

    expected = expected_table_names()
    created = set(inspect(connection).get_table_names(schema="public"))
    missing = expected - created
    if missing:
        names = ", ".join(sorted(missing))
        raise RuntimeError(f"Recovery verification failed; missing tables: {names}")
    return sorted(expected)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create the schema. Without this flag the command is check-only.",
    )
    parser.add_argument(
        "--confirm",
        metavar=CONFIRMATION_TEXT,
        help="Required exact confirmation text when --apply is used.",
    )
    parser.add_argument(
        "--allow-production-recovery",
        action="store_true",
        help="Additional manual override required when IS_PRODUCTION is production.",
    )
    args = parser.parse_args()

    try:
        require_safe_request(
            apply=args.apply,
            confirmation=args.confirm,
            environment=settings.IS_PRODUCTION,
            allow_production_recovery=args.allow_production_recovery,
        )
    except ValueError as error:
        parser.error(str(error))

    url = make_url(settings.DATABASE_URL)
    if url.get_backend_name() != "postgresql":
        parser.error("Database recovery requires PostgreSQL")

    target = f"host={url.host}, port={url.port or 5432}, database={url.database}"
    print(f"Target: {target}")
    print(f"Model tables: {', '.join(sorted(expected_table_names()))}")
    if not args.apply:
        print(
            "Check-only: no connection was opened and no changes were made. "
            f"To restore an empty database, add --apply --confirm {CONFIRMATION_TEXT}."
        )
        return

    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            tables = restore_empty_database(connection)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    except Exception as error:
        # Driver exception messages can contain credentials or server details.
        raise SystemExit(
            f"Database recovery failed ({type(error).__name__}); transaction rolled back"
        ) from None
    finally:
        engine.dispose()

    print(f"Recovery completed and verified: {len(tables)} tables created.")
    print("No roles, accounts, course data, or object-storage files were restored.")


if __name__ == "__main__":
    main()
