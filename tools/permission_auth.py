from uuid import UUID
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from data_model.core_database import get_db
from data_model.data_model import Account, Roles
from dependencies.auth import get_current_session
from dependencies.csrf import verify_csrf


def resolve_account(db: Session, session: dict) -> dict:
    account = db.execute(
        select(Account.id.label("account_id"), Roles.role_name.label("role"), Account.is_active)
        .join(Roles, Roles.id == Account.role_id)
        .where(Account.user_id == UUID(session["user_id"]))
    ).all()
    if not account:
        raise HTTPException(401, "Account not found")
    if len(account) != 1:
        raise HTTPException(403, "Ambiguous account; contact administrator")
    account = account[0]
    if not account.is_active:
        raise HTTPException(403, "Account disabled")
    return {"account_id": account.account_id, "user_id": session["user_id"], "role": account.role}


async def permission_auth(db: Session = Depends(get_db), session: dict = Depends(verify_csrf)):
    """写接口：会话 + CSRF + 当前数据库角色。"""
    return resolve_account(db, session)


async def permission_read_auth(db: Session = Depends(get_db), session: dict = Depends(get_current_session)):
    """读接口：会话 + 当前数据库角色，不要求 CSRF。"""
    return resolve_account(db, session)
