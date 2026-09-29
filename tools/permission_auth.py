from dependencies.csrf import verify_csrf
from data_model.core_database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import Depends, HTTPException
from data_model.data_model import Account, Roles

async def permission_auth(
    db: Session = Depends(get_db),
    session: dict = Depends(verify_csrf)
):
    existing_account = db.execute(
        select(Account.id.label("account_id"),
               Roles.role_name.label("role"))
        .select_from(Account)
        .join(Roles, Roles.id == Account.role_id)
        .where(Account.user_id == session["user_id"])
    ).first()
    if existing_account is None:
        raise HTTPException(status_code=404, detail="Account not exist")
    return {
        "account_id": existing_account.account_id,
        "role": existing_account.role,
    }