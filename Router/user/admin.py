"""管理员配置账号；角色只接受数据库已有角色，禁止资料页自行提权。"""

from uuid import UUID
from typing import Literal
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, or_, text
from sqlalchemy.orm import Session
from data_model.core_database import get_db
from data_model.data_model import Account, User, Roles
from tools.permission_auth import permission_auth, permission_read_auth

router = APIRouter(prefix="/admin", tags=["account administration"])


class AccountUpdate(BaseModel):
    role: Literal["user", "manager", "administer"]
    is_active: bool


def require_admin(account):
    if account["role"] != "administer":
        raise HTTPException(403, "Administrator required")


@router.get("/accounts")
def list_accounts(
    search: str = Query("", max_length=100),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    account=Depends(permission_read_auth),
):
    require_admin(account)
    query = (
        select(Account, User.user_name, Roles.role_name)
        .join(User, User.id == Account.user_id)
        .join(Roles, Roles.id == Account.role_id)
    )
    if search.strip():
        query = query.where(
            or_(
                User.user_name.ilike(f"%{search.strip()}%"),
                Account.email.ilike(f"%{search.strip()}%"),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(
        query.order_by(Account.id).offset((page - 1) * 50).limit(50)
    ).all()
    return {
        "total": total,
        "page": page,
        "accounts": [
            {
                "account_id": str(a.id),
                "user_name": name,
                "email": a.email,
                "role": role,
                "is_active": a.is_active,
            }
            for a, name, role in rows
        ],
    }


@router.put("/accounts/{account_id}")
def update_account(
    account_id: UUID,
    data: AccountUpdate,
    db: Session = Depends(get_db),
    account=Depends(permission_auth),
):
    require_admin(account)
    if db.bind.dialect.name == "postgresql":
        # 串行检查最后一个管理员，防止两个管理员同时移除对方造成无管理员状态。
        db.execute(text("SELECT pg_advisory_xact_lock(7241008)"))
    target = db.scalar(
        select(Account).where(Account.id == account_id).with_for_update()
    )
    if not target:
        raise HTTPException(404, "Account not found")
    role = db.scalar(select(Roles).where(Roles.role_name == data.role))
    if not role:
        raise HTTPException(409, "Role is not configured")
    current_role = db.get(Roles, target.role_id).role_name
    if target.id == account["account_id"] and (
        not data.is_active or data.role != "administer"
    ):
        raise HTTPException(
            409, "Cannot disable or demote your own administrator account"
        )
    if current_role == "administer" and (
        not data.is_active or data.role != "administer"
    ):
        count = db.scalar(
            select(func.count())
            .select_from(Account)
            .join(Roles, Roles.id == Account.role_id)
            .where(Account.is_active.is_(True), Roles.role_name == "administer")
        )
        if count <= 1:
            raise HTTPException(409, "At least one active administrator is required")
    target.role_id = role.id
    target.is_active = data.is_active
    db.commit()
    return {"message": "Account updated"}
