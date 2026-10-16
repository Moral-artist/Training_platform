import math
from datetime import datetime
from fastapi import Depends, HTTPException, Response, APIRouter, Query
from sqlalchemy.orm import Session
from data_model.core_database import get_db
from sqlalchemy import select, func, or_, delete
from sqlalchemy.exc import IntegrityError
from data_model.data_model import (
    Systems,
    SystemLesson,
    Lessons,
    Account,
    VideoAsset,
    LessonAccess,
    User,
)
from schema.lesson import LessonForm
from tools.permission_auth import permission_auth, permission_read_auth
from service.lesson_access import (
    visible_lesson_condition,
    require_lesson_access,
    can_manage_lesson,
)
from core.playback_token import issue_playback_token
from service.video_limits import rate_limit
from uuid import UUID
from data_model.config import settings
import logging
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lessons", tags=["lessons"])


MEMBERSHIP_LEVEL = {
    "free":0,
    "basic":1,
    "pro":2,
}

@router.post("/systemsubmit")
async def systemsubmit(
    system_name: str = Query(..., min_length=1, max_length=200),
    db: Session = Depends(get_db),
    existing_account: dict = Depends(permission_auth),
):
    if existing_account["role"] != "administer":
        raise HTTPException(status_code=403, detail="Administrator required")

    system_name = system_name.lower().strip()
    if not system_name:
        raise HTTPException(422, "System name cannot be blank")
    existing_systm = db.scalar(
        select(Systems).where(Systems.system_name == system_name)
    )
    if existing_systm is not None:
        raise HTTPException(status_code=400, detail="System already exists")

    try:
        new_system = Systems(
            system_name=system_name,
            created_at=datetime.now(),
            create_by=existing_account["account_id"],
        )
        db.add(new_system)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Updating system failed")
    return {"message": "System successfully updated"}


def lesson_summary(db: Session, lesson: Lessons):
    asset = db.get(VideoAsset, lesson.video_asset_id) if lesson.video_asset_id else None
    return {
        "lesson_id": lesson.id,
        "lesson_name": lesson.lesson_name,
        "description": lesson.description,
        "updated_at": lesson.update_at,
        "video_status": asset.status if asset else "migration_pending",
        "video_asset_id": str(asset.id) if asset else None,
        "revision": lesson.revision,
        "system_id": db.scalar(
            select(SystemLesson.system_id).where(SystemLesson.lesson_id == lesson.id)
        ),
    }


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

    query = (
        select(Lessons)
        .join(
            SystemLesson,
            SystemLesson.lesson_id == Lessons.id
        )
        .where(
            SystemLesson.system_id == system_id,
            Lessons.deleted_at.is_(None)
        )
    )

    total = db.scalar(
        select(func.count())
        .select_from(query.subquery())
    ) or 0

    # 一次查出分页课程和授权状态
    rows = db.execute(
        query.with_only_columns(
            Lessons,
            visible_lesson_condition(account).label("can_access")
        )
        .order_by(Lessons.id)
        .limit(page_size)
        .offset((current_page - 1) * page_size)
    ).all()

    lesson_list = []

    for lesson, can_access in rows:
        item = lesson_summary(db, lesson)

        item["can_access"] = bool(can_access)

        lesson_list.append(item)

    return {
        "total_lessons": total,
        "total_pages": math.ceil(total / page_size),
        "current_page": current_page,
        "lessonlist": lesson_list,
    }


@router.post("/lessonsubmit")
async def lessonsubmit(
    lesson_data: LessonForm,
    db: Session = Depends(get_db),
    existing_account: dict = Depends(permission_auth),
):
    if existing_account["role"] not in {"administer", "manager"}:
        raise HTTPException(status_code=403, detail="Administrator required")
    if lesson_data.request_id:
        prior = db.scalar(
            select(Lessons).where(Lessons.request_id == lesson_data.request_id)
        )
        if prior:
            if prior.created_by != existing_account["account_id"]:
                raise HTTPException(409, "Request identifier conflict")
            if (
                prior.lesson_name != lesson_data.lesson_name.strip()
                or prior.description != lesson_data.description.strip()
                or prior.video_asset_id != lesson_data.video_asset_id
                or db.scalar(
                    select(SystemLesson.system_id).where(
                        SystemLesson.lesson_id == prior.id
                    )
                )
                != lesson_data.system_id
            ):
                raise HTTPException(409, "Request content changed")
            return {"message": "Lesson already created", "lesson_id": prior.id}
    asset = db.get(VideoAsset, lesson_data.video_asset_id)
    if (
        asset
        and existing_account["role"] != "administer"
        and asset.created_by != existing_account["account_id"]
    ):
        raise HTTPException(403, "No access to this video")
    if asset is None or asset.status not in {"uploaded", "processing", "ready"}:
        raise HTTPException(409, "Video upload must be completed first")
    if not lesson_data.lesson_name.strip() or not lesson_data.description.strip():
        raise HTTPException(422, "Lesson name and description cannot be blank")

    existing_system = db.scalar(
        select(Systems).where(Systems.id == lesson_data.system_id)
    )
    if existing_system is None:
        raise HTTPException(status_code=404, detail="System not exist")
    try:
        new_lesson = Lessons(
            request_id=lesson_data.request_id,
            lesson_name=lesson_data.lesson_name.strip(),
            description=lesson_data.description.strip(),
            video_asset_id=lesson_data.video_asset_id,
            lesson_video_url=None,
            created_at=datetime.now(),
            update_at=datetime.now(),
            created_by=existing_account["account_id"],
        )

        db.add(new_lesson)
        db.flush()
        new_system_lesson = SystemLesson(
            lesson_id=new_lesson.id, system_id=lesson_data.system_id
        )
        db.add(new_system_lesson)
        db.commit()
        return {"message": "Lesson successfully created", "lesson_id": new_lesson.id}
    except IntegrityError as e:
        db.rollback()
        logger.exception("Failed to create lesson")

        print("数据库原始错误:", e.orig)
        print("SQL语句:", e.statement)
        print("SQL参数:", e.params)
        if lesson_data.request_id:
            prior = db.scalar(
                select(Lessons).where(Lessons.request_id == lesson_data.request_id)
            )
            if (
                prior
                and prior.created_by == existing_account["account_id"]
                and prior.video_asset_id == lesson_data.video_asset_id
                and prior.lesson_name == lesson_data.lesson_name.strip()
                and prior.description == lesson_data.description.strip()
                and db.scalar(
                    select(SystemLesson.system_id).where(
                        SystemLesson.lesson_id == prior.id
                    )
                )
                == lesson_data.system_id
            ):
                return {"message": "Lesson already created", "lesson_id": prior.id}
        raise HTTPException(status_code=400, detail="Updating lesson failed")


@router.get("/systems")
async def getsystems(
    db: Session = Depends(get_db),
    account: dict = Depends(permission_read_auth),
):
    systems = db.scalars(select(Systems)).all()
    return [
        {"system_id": system.id, "system_name": system.system_name}
        for system in systems
    ]


@router.delete("/systems_delete/{system_id}")
async def deletesystem(
        system_id: int,
        db: Session = Depends(get_db),
        account: dict = Depends(permission_auth),
):
    if account["role"]!="administer" and account["role"] != "manager":
        raise HTTPException(409, "Permission denied")
    try:
        current_system = db.get(Systems, system_id)
        if current_system is None:
            raise HTTPException(404, detail="System not exist")
        db.delete(current_system)
        db.commit()
        return {"message": "System successfully deleted"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "delete system failed")


@router.delete("/systems/{system_id}/lessons/{lesson_id}")
async def deletesystem_lesson(
        system_id: int,
        lesson_id: int,
        db: Session = Depends(get_db),
        account: dict = Depends(permission_auth),
):
    if account["role"] != "administer" and account["role"] != "manager":
        raise HTTPException(409, "Permission denied")
    try:
        current_system_lesson = db.get(SystemLesson, (system_id,lesson_id))
        if current_system_lesson is None:
            raise HTTPException(404, detail="System Lesson not exist")
        db.delete(current_system_lesson)
        db.commit()
        return {"message": "Lesson System successfully deleted"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "delete system failed")

@router.get("/alllessons")
async def getalllessons(
    db: Session = Depends(get_db),
    account: dict = Depends(permission_read_auth),
):
    # if MEMBERSHIP_LEVEL[account['membership_level']]<MEMBERSHIP_LEVEL['pro']:
    #     raise HTTPException(403, "You dont have access")
    try:
        all_lessons = db.execute(
            select(
                Systems.system_name.label("system_name"),
                Lessons.lesson_name.label("lesson_name"),
                Lessons.id.label("lesson_id"),
            )
            .select_from(Systems)
            .join(SystemLesson, SystemLesson.system_id == Systems.id)
            .join(Lessons, Lessons.id == SystemLesson.lesson_id)
            # .where(visible_lesson_condition(account))
        ).all()

        grouped = {}
        for item in all_lessons:
            if item.system_name not in grouped:
                grouped[item.system_name] = []

            grouped[item.system_name].append(
                {
                    "lesson_id": item.lesson_id,
                    "lesson_name": item.lesson_name,
                }
            )

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

@router.get("/manage_lessons")
def manage_lessons(
    current_page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query("", max_length=200),
    db: Session = Depends(get_db),
    account: dict = Depends(permission_read_auth),
):
    role = account["role"]
    print(role)
    if role not in {"administer", "manager"}:
        raise HTTPException(
            status_code=403,
            detail="No course management permission"
        )

    query = select(Lessons).where(
        Lessons.deleted_at.is_(None)
    )

    # Manager 只能查询自己创建的课程
    if role == "manager":
        query = query.where(
            Lessons.created_by == account["account_id"]
        )

    # 后端搜索
    keyword = keyword.strip()

    if keyword:
        name_condition = Lessons.lesson_name.ilike(
            f"%{keyword}%"
        )

        if keyword.isdigit():
            query = query.where(
                or_(
                    name_condition,
                    Lessons.id == int(keyword)
                )
            )
        else:
            query = query.where(name_condition)

    # 先统计符合条件的课程数量
    total = db.scalar(
        select(func.count())
        .select_from(query.subquery())
    ) or 0

    # 只查询当前页
    lessons = db.scalars(
        query
        .order_by(Lessons.id.desc())
        .limit(page_size)
        .offset((current_page - 1) * page_size)
    ).all()

    return {
        "total_lessons": total,
        "total_pages": (total + page_size - 1) // page_size,
        "current_page": current_page,
        "lessonlist": [
            {
                "lesson_id": lesson.id,
                "lesson_name": lesson.lesson_name,
                "revision": lesson.revision,
                "can_manage": True,
            }
            for lesson in lessons
        ]
    }
@router.get("/{lesson_id}/detail")
def lesson_detail(
    lesson_id: int,
    db: Session = Depends(get_db),
    account: dict = Depends(permission_read_auth),
):
    lesson = require_lesson_access(db, account, lesson_id)
    return {
        **lesson_summary(db, lesson),
        "can_manage": can_manage_lesson(db, account, lesson),
    }


@router.post("/{lesson_id}/play")
async def play_lesson(
    lesson_id: int,
    response: Response,
    db: Session = Depends(get_db),
    account: dict = Depends(permission_auth),
):
    lesson = require_lesson_access(db, account, lesson_id)
    asset = db.get(VideoAsset, lesson.video_asset_id) if lesson.video_asset_id else None
    if asset is None or asset.status != "ready" or not asset.master_playlist_key:
        raise HTTPException(409, "Video is not ready")
    await rate_limit(account["account_id"], "play", 60, 600)
    data = issue_playback_token(
        account["account_id"], asset.id, asset.master_playlist_key
    )
    response.headers["Cache-Control"] = "no-store"
    # 不记录播放 URL、Token、Cookie、邮箱。
    import logging

    logging.getLogger("video.audit").info(
        "play account=%s lesson=%s asset=%s", account["account_id"], lesson_id, asset.id
    )
    return data


@router.put("/{lesson_id}/access/{account_id}")
def grant_lesson_access(
    lesson_id: int,
    account_id: UUID,
    db: Session = Depends(get_db),
    account: dict = Depends(permission_auth),
):
    if account["role"] != "administer":
        raise HTTPException(403, "Administrator required")
    lesson = db.get(Lessons, lesson_id)
    if (
        lesson is None
        or lesson.deleted_at is not None
        or db.get(Account, account_id) is None
    ):
        raise HTTPException(404, "Lesson or account not found")
    if db.get(LessonAccess, (account_id, lesson_id)) is None:
        db.add(
            LessonAccess(
                account_id=account_id,
                lesson_id=lesson_id,
                granted_by=account["account_id"],
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            if db.get(LessonAccess, (account_id, lesson_id)) is None:
                raise HTTPException(409, "Grant failed")
    return {"message": "Access granted"}


@router.delete("/{lesson_id}/access/{account_id}")
def revoke_lesson_access(
    lesson_id: int,
    account_id: UUID,
    db: Session = Depends(get_db),
    account: dict = Depends(permission_auth),
):
    if account["role"] != "administer" and account["role"] != "manager":
        raise HTTPException(403, "Administrator required")
    grant = db.get(LessonAccess, (account_id, lesson_id))
    if grant:
        db.delete(grant)
        db.commit()
    return {
        "message": "Access revoked",
        "existing_token_max_seconds": min(600, max(120, settings.PLAYBACK_TOKEN_TTL)),
    }


@router.get("/access_accounts")
def access_accounts(
    search: str = Query("", max_length=100),
    db: Session = Depends(get_db),
    account: dict = Depends(permission_read_auth),
):
    """只向管理员返回授权所需账号信息，不返回密码/会话/凭证。"""
    if account["role"] != "administer":
        raise HTTPException(403, "Administrator required")
    query = select(Account.id, Account.email, User.user_name, Account.is_active).join(
        User, User.id == Account.user_id
    )
    if search.strip():
        query = query.where(
            or_(
                Account.email.ilike(f"%{search.strip()}%"),
                User.user_name.ilike(f"%{search.strip()}%"),
            )
        )
    rows = db.execute(query.order_by(User.user_name, Account.id).limit(100)).all()
    return [
        {
            "account_id": str(row.id),
            "email": row.email,
            "user_name": row.user_name,
            "is_active": row.is_active,
        }
        for row in rows
    ]
