import math
from datetime import datetime
from fastapi import Depends, HTTPException, Response, APIRouter, Query
from sqlalchemy.orm import Session
from data_model.core_database import get_db
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from data_model.data_model import Systems, SystemLesson, Lessons, Account, VideoAsset, LessonAccess, User
from schema.lesson import LessonForm
from tools.permission_auth import permission_auth, permission_read_auth
from service.lesson_access import visible_lesson_condition, require_lesson_access
from core.playback_token import issue_playback_token
from service.video_limits import rate_limit
from uuid import UUID
from data_model.config import settings

router = APIRouter(prefix="/lessons", tags=["lessons"])

@router.post("/systemsubmit")
async def systemsubmit(
        system_name: str,
        db:Session= Depends(get_db),
        existing_account: dict = Depends(permission_auth)
):
    if existing_account["role"] != "administer":
        raise HTTPException(status_code=403, detail="Administrator required")

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

def lesson_summary(db: Session, lesson: Lessons):
    asset = db.get(VideoAsset, lesson.video_asset_id) if lesson.video_asset_id else None
    return {"lesson_id": lesson.id, "lesson_name": lesson.lesson_name,
            "description": lesson.description, "updated_at": lesson.update_at,
            "video_status": asset.status if asset else "migration_pending"}


@router.get("/majors/{system_id}/lessonlist")
def lessonlist(
    system_id: int,
    current_page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    account: dict = Depends(permission_read_auth),
):
    if db.get(Systems, system_id) is None:
        raise HTTPException(404, "System not found")
    query = select(Lessons).join(SystemLesson, SystemLesson.lesson_id == Lessons.id).where(
        SystemLesson.system_id == system_id, visible_lesson_condition(account)
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(Lessons.id).limit(page_size).offset((current_page - 1) * page_size)).all()
    return {"total_lessons": total, "total_pages": math.ceil(total / page_size),
            "current_page": current_page, "lessonlist": [lesson_summary(db, row) for row in rows]}


@router.post("/lessonsubmit")
async def lessonsubmit(
        lesson_data: LessonForm,
        db: Session = Depends(get_db),
        existing_account: dict = Depends(permission_auth)
):
    if existing_account["role"] != "administer":
        raise HTTPException(status_code=403, detail="Administrator required")
    asset = db.get(VideoAsset, lesson_data.video_asset_id)
    if asset is None or asset.status not in {"uploaded", "processing", "ready"}:
        raise HTTPException(409, "Video upload must be completed first")
    if not lesson_data.lesson_name.strip() or not lesson_data.description.strip():
        raise HTTPException(422, "Lesson name and description cannot be blank")

    existing_system = db.scalar(select(Systems).where(Systems.id == lesson_data.system_id))
    if existing_system is None:
        raise HTTPException(status_code=404, detail="System not exist")
    try:
        new_lesson = Lessons(
            lesson_name=lesson_data.lesson_name.strip(),
            description=lesson_data.description.strip(),
            video_asset_id=lesson_data.video_asset_id,
            lesson_video_url=None,
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
        return {"message": "Lesson successfully created", "lesson_id": new_lesson.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Updating lesson failed")


@router.get("/systems")
async def getsystems(
        db: Session = Depends(get_db),
        account: dict = Depends(permission_read_auth),
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

@router.get("/alllessons")
async def getalllessons(
        db: Session = Depends(get_db),
        account: dict = Depends(permission_read_auth),
):
    try:
        all_lessons = db.execute(
            select(Systems.system_name.label('system_name'),
                   Lessons.lesson_name.label('lesson_name'),
                   Lessons.id.label('lesson_id'),)
            .select_from(Systems)
            .join(SystemLesson, SystemLesson.system_id == Systems.id)
            .join(Lessons, Lessons.id == SystemLesson.lesson_id)
            .where(visible_lesson_condition(account))
        ).all()

        grouped = {}
        for item in all_lessons:
            if item.system_name not in grouped:
                grouped[item.system_name] = []

            grouped[item.system_name].append({
                "lesson_id": item.lesson_id,
                "lesson_name": item.lesson_name,
            })

        return [
            {
                "system_name": system_name,
                "lessons": lessons,
            }
            for system_name, lessons in grouped.items()
        ]

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Cannot get all lessons")



@router.get("/{lesson_id}/detail")
def lesson_detail(lesson_id: int, db: Session = Depends(get_db), account: dict = Depends(permission_read_auth)):
    return lesson_summary(db, require_lesson_access(db, account, lesson_id))


@router.post("/{lesson_id}/play")
async def play_lesson(lesson_id: int, response: Response, db: Session = Depends(get_db), account: dict = Depends(permission_auth)):
    lesson = require_lesson_access(db, account, lesson_id)
    asset = db.get(VideoAsset, lesson.video_asset_id) if lesson.video_asset_id else None
    if asset is None or asset.status != "ready" or not asset.master_playlist_key:
        raise HTTPException(409, "Video is not ready")
    await rate_limit(account["account_id"], "play", 60, 600)
    data = issue_playback_token(account["account_id"], asset.id, asset.master_playlist_key)
    response.headers["Cache-Control"] = "no-store"
    # 不记录播放 URL、Token、Cookie、邮箱。
    import logging
    logging.getLogger("video.audit").info("play account=%s lesson=%s asset=%s", account["account_id"], lesson_id, asset.id)
    return data


@router.put("/{lesson_id}/access/{account_id}")
def grant_lesson_access(lesson_id: int, account_id: UUID, db: Session = Depends(get_db), account: dict = Depends(permission_auth)):
    if account["role"] != "administer":
        raise HTTPException(403, "Administrator required")
    if db.get(Lessons, lesson_id) is None or db.get(Account, account_id) is None:
        raise HTTPException(404, "Lesson or account not found")
    if db.get(LessonAccess, (account_id, lesson_id)) is None:
        db.add(LessonAccess(account_id=account_id, lesson_id=lesson_id, granted_by=account["account_id"]))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            if db.get(LessonAccess, (account_id, lesson_id)) is None:
                raise HTTPException(409, "Grant failed")
    return {"message": "Access granted"}


@router.delete("/{lesson_id}/access/{account_id}")
def revoke_lesson_access(lesson_id: int, account_id: UUID, db: Session = Depends(get_db), account: dict = Depends(permission_auth)):
    if account["role"] != "administer":
        raise HTTPException(403, "Administrator required")
    grant = db.get(LessonAccess, (account_id, lesson_id))
    if grant:
        db.delete(grant)
        db.commit()
    return {"message": "Access revoked", "existing_token_max_seconds": min(600, max(120, settings.PLAYBACK_TOKEN_TTL))}


@router.get("/access_accounts")
def access_accounts(search: str = Query("", max_length=100), db: Session = Depends(get_db), account: dict = Depends(permission_read_auth)):
    """只向管理员返回授权所需账号信息，不返回密码/会话/凭证。"""
    if account["role"] != "administer":
        raise HTTPException(403, "Administrator required")
    query = select(Account.id, Account.email, User.user_name, Account.is_active).join(User, User.id == Account.user_id)
    if search.strip():
        query = query.where(or_(Account.email.ilike(f"%{search.strip()}%"), User.user_name.ilike(f"%{search.strip()}%")))
    rows = db.execute(query.order_by(User.user_name, Account.id).limit(100)).all()
    return [{"account_id": str(row.id), "email": row.email, "user_name": row.user_name, "is_active": row.is_active} for row in rows]
