from fastapi import Depends, HTTPException, APIRouter, Response
from dependencies.auth import get_current_session
from dependencies.csrf import verify_csrf
from schema.user import EditUser
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from data_model.core_database import get_db
from data_model.data_model import (User, Account, Roles,
                                   CustomedPlan, PlanLesson, Lessons)

router = APIRouter(prefix="/user", tags=["user_info"])

@router.get("/user_info")
async def me(
    response: Response,
    session: dict = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    user_id = session["user_id"]

    user_info = db.execute(
        select(User.user_name.label("user_name"),
               Roles.role_name.label("role"))
        .select_from(User)
        .join(Account, Account.user_id == User.id)
        .join(Roles, Roles.id == Account.role_id)
        .where(User.id == user_id)
    ).first()
    if not user_info:
        raise HTTPException(status_code=401, detail="User not found")

    csrf_token = session["csrf_token"]
    response.headers["Cache-Control"] = "no-store"

    return {
        "user_name": user_info.user_name,
        "role": user_info.role,
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

@router.get("/my_lessons")
async def my_lessons(
        session: dict = Depends(get_current_session),
        db: Session = Depends(get_db),
):
    try:
        my_lessons = db.execute(
            select(CustomedPlan.plan_name.label("plan_name"),
                   CustomedPlan.id.label("plan_id"),
                   CustomedPlan.source_type.label("source_type"),
                   Lessons.id.label("lesson_id"),
                   PlanLesson.lesson_order.label("lesson_order"),
                   Lessons.lesson_name.label("lesson_name"),
                   PlanLesson.completed.label("completed"),)
            .select_from(CustomedPlan)
            .join(PlanLesson, PlanLesson.plan_id==CustomedPlan.id)
            .join(Lessons, Lessons.id==PlanLesson.lesson_id)
            .where(CustomedPlan.user_id == session["user_id"])
        ).all()

        grouped={}
        for item in my_lessons:
            key = (
                item.plan_id,
                item.plan_name,
                item.source_type
            )
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(
                {
                    "lesson_id": item.lesson_id,
                    "lesson_name": item.lesson_name,
                    "lesson_order": item.lesson_order,
                    "completed": item.completed,
                }
            )
        return [{
            "plan_name": plan_info[1],
            "source_type": plan_info[2],
            "lessons": lesson
        } for plan_info, lesson in grouped.items()]

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Updating information failed")



