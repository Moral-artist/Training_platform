"""Create local test accounts only; never update existing passwords."""

import getpass
import os
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.engine import make_url

from core.security import hash_password
from data_model.config import settings
from data_model.core_database import SessionLocal
from data_model.data_model import Account, Roles, Systems, User


def main():
    url = make_url(settings.DATABASE_URL)
    if (
        os.getenv("TEST_ENVIRONMENT") != "1"
        or url.host not in ("localhost", "127.0.0.1")
        or url.port != 15433
        or url.database != "training_r2_test"
    ):
        raise SystemExit(
            "Only TEST_ENVIRONMENT=1 and local port 15433 / training_r2_test are allowed"
        )
    password = getpass.getpass(
        "Set a password for three test accounts (at least 12 characters): "
    )
    if len(password) < 12 or password != getpass.getpass("Repeat password: "):
        raise SystemExit("Password too short or does not match; no changes")
    with SessionLocal.begin() as db:
        emails = ["admin@example.com", "manager@example.com", "student@example.com"]
        if db.scalar(select(Account.id).where(Account.email.in_(emails)).limit(1)):
            raise SystemExit(
                "Test accounts already exist; no existing account will be changed"
            )
        admin_id = None
        for label, role_name in [
            ("admin", "administer"),
            ("manager", "manager"),
            ("student", "user"),
        ]:
            roles = db.scalars(select(Roles).where(Roles.role_name == role_name)).all()
            if len(roles) > 1:
                raise SystemExit("Duplicate role names; resolve before seeding")
            role = (
                roles[0]
                if roles
                else Roles(id=f"video_test_{role_name}", role_name=role_name)
            )
            if not roles:
                db.add(role)
                db.flush()
            user = User(
                id=uuid4(), user_name=f"Video Test {label}", character="engineer"
            )
            db.add(user)
            db.flush()
            account = Account(
                id=uuid4(),
                user_id=user.id,
                email=f"{label}@example.com",
                password=hash_password(password),
                role_id=role.id,
                is_active=True,
            )
            db.add(account)
            db.flush()
            if label == "admin":
                admin_id = account.id
        if (
            db.scalar(select(Systems).where(Systems.system_name == "electrical"))
            is None
        ):
            db.add(Systems(system_name="electrical", create_by=admin_id))
    print(
        "Created admin@example.com / manager@example.com / student@example.com and electrical."
    )
    print(
        "All three accounts use the password you entered. No course permissions were granted."
    )


if __name__ == "__main__":
    main()
