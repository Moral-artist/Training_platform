from fastapi import HTTPException, APIRouter, Depends, Response, Cookie
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from data_model.core_database import get_db
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from data_model.data_model import User
from data_model.data_model import Account
from data_model.data_model import Roles

import os

from service.session import create_session, SESSION_TTL, delete_session
from schema.auth import RegisterRequest, LoginRequest, TokenResponse
from dependencies.csrf import verify_csrf

IS_PRODUCTION = os.getenv("IS_PRODUCTION")=="production"

router = APIRouter(
    prefix="/auth",
    tags=['Authentication']
)

@router.post("/register")
def register(
        data: RegisterRequest,
        db: Session = Depends(get_db),
):
    email = str(data.email).lower()
    existing_account = db.scalar(
        select(Account).where(Account.email == email)
    )

    if existing_account:
        raise HTTPException(
            status_code=409,
            detail="Account with this email already exists",
        )

    default_role = db.scalar(
        select(Roles).where(Roles.role_name == "user")
    )

    if default_role is None:
        raise HTTPException(
            status_code=500,
            detail="Default role does not exist",
        )
    try:
        user = User(
            user_name=data.user_name,
        )
        db.add(user)
        db.flush()

        account = Account(
            user_id=user.id,
            email=email,
            password=hash_password(data.password),
            role_id=default_role.id
        )
        db.add(account)
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Account is not consistent with this email",
        )
    return{
        "message": "Create account successfully",
        "user_id": user.id
    }

@router.post("/login")
async def login(
        data: LoginRequest,
        response: Response,
        db: Session = Depends(get_db),
):
    email = str(data.email).lower()
    existing_account = db.scalar(select(Account).where(Account.email == email))
    if existing_account is None:
        raise HTTPException(
            status_code=400,
            detail="Account has not been created",
        )
    if not verify_password(data.password, existing_account.password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    session_id, csrf_token = await create_session(str(existing_account.user_id))
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure = IS_PRODUCTION,
        samesite = "lax",
        max_age= SESSION_TTL,
        path="/"
    )
    return {
        "message": "login success",
        "csrf_token": csrf_token,
    }

@router.post("/logout")
async def logout(
    response: Response,
    session_id: str | None = Cookie(default=None),
    session: dict = Depends(verify_csrf),
):
    await delete_session(session_id)
    response.delete_cookie(
        key="session_id",
        httponly=True,
        secure = IS_PRODUCTION,
        path='/',
        samesite='lax'
    )
    return {
        "message": "logout success",
    }


