"""目录公开不等于详情公开：所有敏感操作在后端重新检查。"""

from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from data_model.data_model import LessonAccess, Lessons, VideoAsset


def can_manage_lesson(db, account, lesson):
    if not account:
        return False
    if account["role"] == "administer" or lesson.created_by == account["account_id"]:
        return True
    asset = db.get(VideoAsset, lesson.video_asset_id) if lesson.video_asset_id else None
    return bool(asset and asset.created_by == account["account_id"])


def visible_lesson_condition(account):
    active = Lessons.deleted_at.is_(None)
    if account["role"] == "administer":
        return active
    return active & or_(
        Lessons.created_by == account["account_id"],
        Lessons.video_asset_id.in_(
            select(VideoAsset.id).where(VideoAsset.created_by == account["account_id"])
        ),
        Lessons.id.in_(
            select(LessonAccess.lesson_id).where(
                LessonAccess.account_id == account["account_id"]
            )
        ),
    )


def has_lesson_access(db, account, lesson):
    return bool(
        account
        and (
            can_manage_lesson(db, account, lesson)
            or db.get(LessonAccess, (account["account_id"], lesson.id))
        )
    )


def require_lesson_access(db: Session, account: dict, lesson_id: int):
    lesson = db.get(Lessons, lesson_id)
    if lesson is None or lesson.deleted_at is not None:
        raise HTTPException(404, "Lesson not found")
    if not has_lesson_access(db, account, lesson):
        raise HTTPException(403, "No lesson permission")
    return lesson
