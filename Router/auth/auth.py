from fastapi import HTTPException, APIRouter, Depends, Response, Cookie
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from data_model.core_database import get_db
from core.security import (
    hash_password,
    verify_password,
)
from data_model.data_model import User
from data_model.data_model import Account
from data_model.data_model import Roles
import secrets
import os
import json
from service.session import create_session, SESSION_TTL, delete_session
from schema.auth import RegisterRequest, LoginRequest, ResetPasswordRequest
from dependencies.csrf import verify_csrf
from tools.email_tool import send_verify_email
from tools.email_otp import verify_email_challenge, create_email_challenge

IS_PRODUCTION = os.getenv("IS_PRODUCTION")=="production"

router = APIRouter(
    prefix="/auth",
    tags=['Authentication']
)

@router.post("/pre_register")
async def pre_register(
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

    hashed_password = hash_password(data.password)
    challenge_id, code =await create_email_challenge(
        email, data.user_name, hashed_password,default_role.id
    )
    send_verify_email(email,code)
    return {
        "message": "Have send the email code",
        "challenge_id": challenge_id
    }

@router.post("/verify_register")
async def verify_register(
        code: str,
        challenge_id: str,
        db: Session = Depends(get_db)):
    user_info = await verify_email_challenge(challenge_id, code)
    if user_info is None:
        raise HTTPException(
            status_code=401,
            detail="验证码已过期或注册信息不存在"
        )

    try:
        user = User(
            user_name=user_info["user_name"],
        )
        db.add(user)
        db.flush()

        account = Account(
            user_id=user.id,
            email=user_info["email"],
            password=user_info["hash_password"],
            role_id=user_info["role_id"]
        )
        db.add(account)
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Account is not consistent with this email",
        )
    return {
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
    if session_id is not None:
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

@router.post("/pre_reset")
async def pre_reset(
        data:ResetPasswordRequest,
        db: Session = Depends(get_db),
):
    email = str(data.email).lower()
    existing_account = db.scalar(select(Account).where(Account.email == email))
    if existing_account is None:
        raise HTTPException(
            status_code=409,
            detail="Account does not exist",
        )
    hashed_password = hash_password(data.new_password)
    challenge_id, code = await create_email_challenge(email=email, hashed_password=hashed_password)
    send_verify_email(email,code)
    return {
        "message": "Have send the email code",
        "challenge_id": challenge_id
    }

@router.post("/verify_reset")
async def verify_reset(
        code: str,
        challenge_id: str,
        response: Response,
        db: Session = Depends(get_db),
        session_id: str | None = Cookie(default=None)
):
    reset_info = await verify_email_challenge(challenge_id, code)
    if reset_info is None:
        raise HTTPException(
            status_code=401,
            detail="验证码已过期或注册信息不存在"
        )
    try:
        db.execute(
            update(Account)
            .where(Account.email==reset_info["email"])
            .values(password=reset_info["hash_password"])
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=410,
            detail="Update encountered error",
        )
    if session_id is not None:
        await delete_session(session_id)

    response.delete_cookie(
        key="session_id",
        path="/"
    )
    return {
        "message": "Have reset the password",
    }



