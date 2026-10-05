from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from data_model.data_model import LessonAccess, Lessons


def visible_lesson_condition(account: dict):
    # 学员自己加入学习计划不等于获得课程播放授权。
    if account["role"] == "administer":
        return True
    return Lessons.id.in_(select(LessonAccess.lesson_id).where(
        LessonAccess.account_id == account["account_id"]
    ))


def require_lesson_access(db: Session, account: dict, lesson_id: int) -> Lessons:
    lesson = db.get(Lessons, lesson_id)
    if lesson is None:
        raise HTTPException(404, "Lesson not found")
    if account["role"] != "administer" and db.get(
        LessonAccess, (account["account_id"], lesson_id)
    ) is None:
        raise HTTPException(403, "No lesson permission")
    return lesson
