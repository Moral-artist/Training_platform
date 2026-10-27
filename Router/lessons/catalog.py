"""首页只公开课程名称、状态和访问标记，不公开简介/视频对象/播放 URL。"""

import math
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from data_model.core_database import get_db
from data_model.data_model import (
    Systems,
    SystemLesson,
    Lessons,
    LessonAccess,
    VideoAsset,
)
from tools.permission_auth import (
    optional_account,
    permission_auth,
    permission_read_auth,
)
from service.lesson_access import has_lesson_access, can_manage_lesson
from schema.course_management import LessonUpdate
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/lessons", tags=["catalog and management"])


@router.get("/catalog")
def catalog(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    account=Depends(optional_account),
):
    total = db.scalar(
        select(func.count())
        .select_from(SystemLesson)
        .join(Lessons, Lessons.id == SystemLesson.lesson_id)
        .where(Lessons.deleted_at.is_(None))
    ) or 0
    rows = db.execute(
        select(
            SystemLesson.system_id,
            Systems.system_name,
            Lessons,
            VideoAsset.status,
        )
        .join(Systems, Systems.id == SystemLesson.system_id)
        .join(Lessons, Lessons.id == SystemLesson.lesson_id)
        .outerjoin(VideoAsset, VideoAsset.id == Lessons.video_asset_id)
        .where(Lessons.deleted_at.is_(None))
        .order_by(Lessons.id)
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    lesson_ids = [lesson.id for _, _, lesson, _ in rows]
    asset_ids = [
        lesson.video_asset_id for _, _, lesson, _ in rows if lesson.video_asset_id
    ]
    # 只计算当前页的授权和资产归属，避免课程数增加时全表加载。
    grants = (
        set(
            db.scalars(
                select(LessonAccess.lesson_id).where(
                    LessonAccess.account_id == account["account_id"],
                    LessonAccess.lesson_id.in_(lesson_ids),
                )
            ).all()
        )
        if account and lesson_ids
        else set()
    )
    assets = (
        set(
            db.scalars(
                select(VideoAsset.id).where(
                    VideoAsset.created_by == account["account_id"],
                    VideoAsset.id.in_(asset_ids),
                )
            ).all()
        )
        if account and asset_ids
        else set()
    )
    grouped = {}
    for sid, system_name, lesson, status in rows:
        system = grouped.setdefault(
            sid,
            {"system_id": sid, "system_name": system_name, "lessons": []},
        )
        allowed = bool(
            account
            and (
                account["role"] == "administer"
                or lesson.created_by == account["account_id"]
                or lesson.video_asset_id in assets
                or lesson.id in grants
            )
        )
        system["lessons"].append(
            {
                "lesson_id": lesson.id,
                "lesson_name": lesson.lesson_name,
                "video_status": status or "migration_pending",
                "can_access": allowed,
                "access_reason": (
                    "allowed"
                    if allowed
                    else "login_required" if not account else "grant_required"
                ),
            }
        )
    return {
        "items": list(grouped.values()),
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": math.ceil(total / limit) if total else 0,
    }


def managed(db, account, lesson_id, lock=False):
    lesson = (
        db.scalar(select(Lessons).where(Lessons.id == lesson_id).with_for_update())
        if lock
        else db.get(Lessons, lesson_id)
    )
    if not lesson or lesson.deleted_at is not None:
        raise HTTPException(404, "Lesson not found")
    if not can_manage_lesson(db, account, lesson):
        raise HTTPException(403, "No course management permission")
    return lesson


@router.put("/{lesson_id}")
def update_lesson(
    lesson_id: int,
    data: LessonUpdate,
    db: Session = Depends(get_db),
    account=Depends(permission_auth),
):
    lesson = managed(db, account, lesson_id, True)
    if lesson.revision != data.revision:
        raise HTTPException(409, "Course changed; reload before editing")
    asset = db.get(VideoAsset, data.video_asset_id)
    if not asset or asset.status not in {"uploaded", "processing", "ready"}:
        raise HTTPException(409, "Video upload must be completed first")
    # 原课程绑定的视频可继续保留；新视频必须由当前用户持有或管理员选用。
    if (
        account["role"] != "administer"
        and asset.created_by != account["account_id"]
        and lesson.video_asset_id != asset.id
    ):
        raise HTTPException(403, "No access to this video")
    if not db.get(Systems, data.system_id):
        raise HTTPException(404, "System not found")
    if not data.lesson_name.strip() or not data.description.strip():
        raise HTTPException(422, "Lesson name and description cannot be blank")
    lesson.lesson_name = data.lesson_name.strip()
    lesson.description = data.description.strip()
    lesson.video_asset_id = asset.id
    lesson.update_at = datetime.now(timezone.utc)
    lesson.revision += 1
    from sqlalchemy import delete

    db.execute(delete(SystemLesson).where(SystemLesson.lesson_id == lesson.id))
    db.add(SystemLesson(system_id=data.system_id, lesson_id=lesson.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Course name already exists")
    return {"lesson_id": lesson.id, "revision": lesson.revision}


@router.delete("/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    revision: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    account=Depends(permission_auth),
):
    lesson = managed(db, account, lesson_id, True)
    if lesson.revision != revision:
        raise HTTPException(409, "Course changed; reload before deleting")
    lesson.deleted_at = datetime.now(timezone.utc)
    lesson.revision += 1
    db.commit()
    return {"message": "Course archived", "existing_token_max_seconds": 600}


@router.get("/{lesson_id}/access")
def list_access(
    lesson_id: int, db: Session = Depends(get_db), account=Depends(permission_read_auth)
):
    if account["role"] != "administer":
        raise HTTPException(403, "Administrator required")
    if not db.get(Lessons, lesson_id):
        raise HTTPException(404, "Lesson not found")
    return [
        str(value)
        for value in db.scalars(
            select(LessonAccess.account_id).where(LessonAccess.lesson_id == lesson_id)
        ).all()
    ]
