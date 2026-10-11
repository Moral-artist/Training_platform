"""新环境初始化角色并创建管理员。密码交互输入，绝不覆盖已有账号。"""

import argparse, getpass
from uuid import uuid4
from sqlalchemy import select, text
from data_model.core_database import SessionLocal
from data_model.data_model import Account, User, Roles
from core.security import hash_password
from pydantic import TypeAdapter, EmailStr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
    if not args.apply:
        print("Check-only. Add --apply to create an administrator and missing roles.")
        return
    password = getpass.getpass("Administrator password (12–128 characters): ")
    if not 12 <= len(password) <= 128 or password != getpass.getpass(
        "Repeat password: "
    ):
        raise SystemExit("Invalid password; no changes")
    with SessionLocal.begin() as db:
        if db.bind.dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(7241008)"))
        if db.scalar(select(Account).where(Account.email == email)):
            raise SystemExit("Account exists; no account was changed")
        roles = {}
        for name in ["user", "manager", "administer"]:
            matches = db.scalars(select(Roles).where(Roles.role_name == name)).all()
            if len(matches) > 1:
                raise SystemExit("Duplicate role names; resolve existing data first")
            role = matches[0] if matches else Roles(id=name, role_name=name)
            if not matches:
                db.add(role)
            roles[name] = role
        db.flush()
        user = User(id=uuid4(), user_name="Administrator", character="engineer")
        db.add(user)
        db.flush()
        db.add(
            Account(
                id=uuid4(),
                user_id=user.id,
                email=email,
                password=hash_password(password),
                role_id=roles["administer"].id,
                is_active=True,
            )
        )
    print("Administrator created. No existing passwords or permissions were changed.")


if __name__ == "__main__":
    main()
