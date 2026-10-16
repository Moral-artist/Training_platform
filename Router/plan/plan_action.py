
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete, and_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from data_model.core_database import get_db
from data_model.data_model import (
    TrainingPlan,
    TrainingPlanLesson,
    CustomedPlan,
    PlanLesson,
    Lessons,
    LessonAccess
)
from schema.lesson import TemplatePlan, AddTemplatePlan, AddCustomPlan, LessonItem
from tools.permission_auth import permission_auth, permission_read_auth
from service.lesson_access import require_lesson_access

MEMBERSHIP_LEVEL = {
    "free":0,
    "basic":1,
    "pro":2,
}

router = APIRouter(prefix="/plan", tags=["Plan"])


def validate_items(db, account, items):
    if (
        not items
        or len({i.lesson_id for i in items}) != len(items)
        or len({i.order for i in items}) != len(items)
        or any(i.order < 1 for i in items)
    ):
        raise HTTPException(
            422, "Plan needs distinct lessons and positive distinct orders"
        )
    for item in items:
        require_lesson_access(db, account, item.lesson_id)


def save(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Plan data conflict")


@router.get("/preset_planlist")
def templates(db: Session = Depends(get_db), account=Depends(permission_read_auth)):
    result = []
    for plan in db.scalars(select(TrainingPlan).order_by(TrainingPlan.id)):
        rows = db.execute(
            select(TrainingPlanLesson, Lessons.lesson_name, Lessons.deleted_at)
            .join(Lessons, Lessons.id == TrainingPlanLesson.lesson_id)
            .where(TrainingPlanLesson.plan_id == plan.id)
            .order_by(TrainingPlanLesson.lesson_order)
        ).all()
        result.append(
            {
                "plan_id": plan.id,
                "plan_name": plan.plan_name,
                "description": plan.description,
                "lessons": [
                    {
                        "lesson_id": row.lesson_id,
                        "order": row.lesson_order,
                        "lesson_name": name,
                        "archived": deleted is not None,
                    }
                    for row, name, deleted in rows
                ],
            }
        )
    return result


@router.post("/create_preset_plan")
def create_template(
    data: TemplatePlan, db: Session = Depends(get_db), account=Depends(permission_auth)
):
    if account["role"] not in {"administer", "manager"}:
        raise HTTPException(403, "Manager required")
    validate_items(db, account, data.lesson_list)
    plan = TrainingPlan(
        plan_name=data.plan_name,
        description=data.description,
        created_by=account["account_id"],
    )
    db.add(plan)
    db.flush()
    for item in data.lesson_list:
        db.add(
            TrainingPlanLesson(
                plan_id=plan.id, lesson_id=item.lesson_id, lesson_order=item.order
            )
        )
    save(db)
    return {"plan_id": plan.id}


@router.post("/add_template_plan")
def add_template(
    data: AddTemplatePlan,
    db: Session = Depends(get_db),
    account=Depends(permission_auth),
):
    if MEMBERSHIP_LEVEL[account['membership_level']]<MEMBERSHIP_LEVEL['basic']:
        raise HTTPException(409, "You dont have access, You need to upgrade to Basic")
    if not db.get(TrainingPlan, data.plan_id):
        raise HTTPException(404, "Plan not found")
    rows = db.scalars(
        select(TrainingPlanLesson)
        .where(TrainingPlanLesson.plan_id == data.plan_id)
        .order_by(TrainingPlanLesson.lesson_order)
    ).all()
    items = [LessonItem(lesson_id=i.lesson_id, order=i.lesson_order) for i in rows]
    # validate_items(db, account, items)
    return create_personal(db, account, data.plan_name, items, data.plan_id)


def create_personal(db, account, name, items, template=None):
    try:
        plan = CustomedPlan(
            plan_name=name,
            user_id=account["user_id"],
            template_plan_id=template,
            source_type="preset" if template is not None else "manual",
            status="not_started",
        )

        db.add(plan)
        db.flush()

        # 本次请求中已处理过的课程
        processed_lessons = set()

        for item in items:

            db.add(
                PlanLesson(
                    plan_id=plan.id,
                    lesson_id=item.lesson_id,
                    lesson_order=item.order,
                    completed=False,
                )
            )

            if item.lesson_id in processed_lessons:
                continue

            processed_lessons.add(item.lesson_id)

            existing_access = db.scalar(
                select(LessonAccess)
                .where(
                    LessonAccess.account_id == account["account_id"],
                    LessonAccess.lesson_id == item.lesson_id
                )
            )

            if existing_access is None:
                db.add(
                    LessonAccess(
                        lesson_id=item.lesson_id,
                        account_id=account["account_id"],
                        granted_by=account["account_id"]
                    )
                )

        save(db)

        return {"plan_id": plan.id}

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Create plan failed"
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error"
        )
@router.post("/add_custom_plan")
def add_custom(
    data: AddCustomPlan, db: Session = Depends(get_db), account=Depends(permission_auth)
):
    if MEMBERSHIP_LEVEL[account['membership_level']]<MEMBERSHIP_LEVEL['pro']:
        raise HTTPException(409, "You dont have access, You need to upgrade to PRO")
    # validate_items(db, account, data.lesson_list)
    return create_personal(db, account, data.plan_name, data.lesson_list)


@router.get("/mine")
def mine(db: Session = Depends(get_db), account=Depends(permission_read_auth)):
    result = []
    for plan in db.scalars(
        select(CustomedPlan)
        .where(CustomedPlan.user_id == account["user_id"])
        .order_by(CustomedPlan.id)
    ):
        rows = db.execute(
            select(PlanLesson, Lessons.lesson_name, Lessons.deleted_at)
            .join(Lessons, Lessons.id == PlanLesson.lesson_id)
            .where(PlanLesson.plan_id == plan.id)
            .order_by(PlanLesson.lesson_order)
        ).all()
        result.append(
            {
                "plan_id": plan.id,
                "plan_name": plan.plan_name,
                "status": plan.status,
                "lessons": [
                    {
                        "lesson_id": i.lesson_id,
                        "lesson_name": name,
                        "completed": i.completed,
                        "archived": deleted is not None,
                    }
                    for i, name, deleted in rows
                ],
            }
        )
    return result


class Progress(BaseModel):
    completed: bool


@router.put("/{plan_id}/lessons/{lesson_id}/progress")
def progress(
    plan_id: int,
    lesson_id: int,
    data: Progress,
    db: Session = Depends(get_db),
    account=Depends(permission_auth),
):
    plan = db.scalar(
        select(CustomedPlan).where(CustomedPlan.id == plan_id).with_for_update()
    )
    if not plan or plan.user_id != account["user_id"]:
        raise HTTPException(404, "Plan not found")
    require_lesson_access(db, account, lesson_id)
    item = db.get(PlanLesson, (lesson_id, plan_id))
    if not item:
        raise HTTPException(404, "Plan lesson not found")
    item.completed = data.completed
    item.completed_at = datetime.now(timezone.utc) if data.completed else None
    db.flush()
    items = db.scalars(select(PlanLesson).where(PlanLesson.plan_id == plan_id)).all()
    plan.status = "completed" if all(i.completed for i in items) else "in_progress"
    save(db)
    return {"status": plan.status}


@router.delete("/presetPlan_delete/{preset_plan_id}")
def preset_plan_delete(
        preset_plan_id: int,
        db: Session = Depends(get_db),
        account=Depends(permission_auth),
):
    if account['role']!='manager' and account['role'] != 'administer':
        raise HTTPException(409, "You dont have access, only for manager or administer")

    preset_plan = db.scalar(
        select(TrainingPlan)
        .where(
            TrainingPlan.id == preset_plan_id,
            or_(TrainingPlan.created_by == account['account_id'],
                account['role'] == 'administer'),

        )
    )
    if preset_plan is None:
        raise HTTPException(
            status_code=404,
            detail="Preset Plan not found"
        )
    try:

        db.delete(preset_plan)

        db.commit()

        return {
            "message": "Preset Plan deleted successfully",
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Delete preset plan failed"
        )


@router.delete("/plan_delete/{plan_id}")
def delete_personal_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    account: dict = Depends(permission_auth),
):
    plan = db.scalar(
        select(CustomedPlan)
        .where(
            CustomedPlan.id == plan_id,
            CustomedPlan.user_id == account["user_id"]
        )
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )

    try:
        db.execute(
            delete(PlanLesson)
            .where(PlanLesson.plan_id == plan_id)
        )

        db.delete(plan)

        db.commit()

        return {
            "message": "Plan deleted successfully",
            "plan_id": plan_id
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Delete plan failed"
        )