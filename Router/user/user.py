from fastapi import Depends, HTTPException, APIRouter, Response
from dependencies.auth import get_current_session
from sqlalchemy.orm import Session
from sqlalchemy import select
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
