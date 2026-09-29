import math
from datetime import datetime
from dependencies.csrf import verify_csrf
from fastapi import FastAPI, Depends, HTTPException, Response, APIRouter
from sqlalchemy.orm import Session
from data_model.core_database import get_db
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from data_model.data_model import Systems, SystemLesson, Lessons, Account, Roles
from schema.lesson import LessonForm
from tools.permission_auth import permission_auth
router = APIRouter(prefix="/lessons", tags=["lessons"])

@router.post("/systemsubmit")
async def systemsubmit(
        system_name: str,
        db:Session= Depends(get_db),
        existing_account: dict = Depends(permission_auth)
):
    if existing_account["role"] != "administer":
        raise HTTPException(status_code=400, detail="Account is not administer")

    system_name = system_name.lower().strip()
    existing_systm = db.scalar(
        select(Systems)
        .where(Systems.system_name==system_name)
    )
    if existing_systm is not None:
        raise HTTPException(status_code=400, detail="System already exists")

    try:
        new_system = Systems(
            system_name=system_name,
            created_at=datetime.now(),
            create_by=existing_account["account_id"]
        )
        db.add(new_system)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Updating system failed")
    return {"message": "System successfully updated"}

@router.get("/majors/{system_id}/lessonlist")
async def lessonlist(
        system_id: int,
        current_page: int = 1,
        page_size: int = 10,
        db: Session = Depends(get_db),
):

    existing_system = db.scalar(select(Systems).where(Systems.id == system_id))
    if existing_system is None:
        raise HTTPException(status_code=404, detail="System not exist")
    try:
        selected_lessons = db.scalars(
            select(Lessons)
            .join(SystemLesson,
                  SystemLesson.lesson_id == Lessons.id)
            .where(SystemLesson.system_id == system_id)
            .limit(page_size)
            .offset(page_size*(current_page-1))
            .order_by(Lessons.id)
        ).all()
        total_lessons = db.scalar(
            select(func.count())
            .select_from(SystemLesson)
            .where(SystemLesson.system_id == system_id)
        )
        total_pages = math.ceil(total_lessons / page_size)

        if not selected_lessons:
            raise HTTPException(status_code=404, detail="Lesson not exist")

        return {
            "total_lessons": total_lessons,
            "total_pages": total_pages,
            "current_page": current_page,
            "lessonlist":[{
                "lesson_id": lesson.id,
                "lesson_name": lesson.lesson_name,
                "description": lesson.description,
                "video_url": lesson.lesson_video_url,
                "updated_at": lesson.update_at
            } for lesson in selected_lessons]
        }
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Getting info failed")

@router.post("/lessonsubmit")
async def lessonsubmit(
        lesson_data: LessonForm,
        db: Session = Depends(get_db),
        existing_account: dict = Depends(permission_auth)
):
    if existing_account["role"] != "administer":
        raise HTTPException(status_code=400, detail="Account is not administer")

    existing_system = db.scalar(select(Systems).where(Systems.id == lesson_data.system_id))
    if existing_system is None:
        raise HTTPException(status_code=404, detail="System not exist")
    try:
        new_lesson = Lessons(
            lesson_name=lesson_data.lesson_name,
            description=lesson_data.description,
            lesson_video_url=lesson_data.lesson_video_url,
            created_at=datetime.now(),
            update_at=datetime.now(),
            created_by=existing_account["account_id"]
        )

        db.add(new_lesson)
        db.flush()
        new_system_lesson = SystemLesson(
            lesson_id=new_lesson.id,
            system_id=lesson_data.system_id
        )
        db.add(new_system_lesson)
        db.commit()
        return {"message": "Lesson successfully created"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Updating lesson failed")


@router.get("/systems")
async def getsystems(
        db: Session = Depends(get_db),
):
    systems = db.scalars(
        select(Systems)
    ).all()
    if not systems:
        raise HTTPException(status_code=404, detail="System not exist")
    return [{
        "system_id":system.id,
        "system_name": system.system_name
    } for system in systems]