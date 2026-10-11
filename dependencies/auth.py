"""HttpOnly 会话校验；改密后 auth_version 使所有旧会话失效。"""

from uuid import UUID
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from service.session import get_session
from data_model.core_database import get_db
from data_model.data_model import Account


async def get_current_session(
    session_id: str | None = Cookie(default=None), db: Session = Depends(get_db)
):
    if not session_id:
        raise HTTPException(401, "Not Authenticated")
    session = await get_session(session_id)
    if session is None:
        raise HTTPException(401, "Session expired")
    account = db.scalar(
        select(Account).where(Account.user_id == UUID(session["user_id"]))
    )
    if not account:
        raise HTTPException(401, "Account not found")
    if not account.is_active:
        raise HTTPException(403, "Account disabled")
    if account.auth_version != session.get("auth_version", 0):
        raise HTTPException(401, "Session expired")
    return session
