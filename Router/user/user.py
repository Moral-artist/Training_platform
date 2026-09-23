from fastapi import Depends, HTTPException, APIRouter, Response
from dependencies.auth import get_current_session
from dependencies.csrf import verify_csrf
from schema.user import EditUser
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from data_model.core_database import get_db
from data_model.data_model import User

router = APIRouter(prefix="/user", tags=["user_info"])

@router.get("/user_info")
async def me(
    response: Response,
    session: dict = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    user_id = session["user_id"]

    user_info = db.scalar(select(User).where(User.id == user_id))
    if not user_info:
        raise HTTPException(status_code=401, detail="User not found")

    csrf_token = session["csrf_token"]
    response.headers["Cache-Control"] = "no-store"

    return {
        "user_name": user_info.user_name,
        "csrf_token": csrf_token
    }

@router.post("/edit_profile")
async def edit_profile(
        edit_info: EditUser,
        session: dict = Depends(verify_csrf),
        db: Session = Depends(get_db),
):
    existing_user = db.scalar(select(User).where(User.id == session["user_id"]))
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    if (edit_info.username is None
    or edit_info.character is None):
        raise HTTPException(status_code=400, detail="Username and Character are required")

    try:
        if edit_info.username is not None:
            existing_user.user_name = edit_info.username
        if edit_info.character is not None:
            existing_user.character = edit_info.character
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Updating information failed")
    return {
        "message": "User updated successfully",
    }
