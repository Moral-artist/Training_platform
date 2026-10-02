import math
from datetime import datetime
from dependencies.csrf import verify_csrf
from fastapi import FastAPI, Depends, HTTPException, Response, APIRouter
from sqlalchemy.orm import Session
from data_model.core_database import get_db
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from data_model.data_model import (Systems, SystemLesson, Lessons,
                                   Account, Roles, PlanLesson, CustomedPlan,
                                   TrainingPlanLesson, TrainingPlan)
from schema.lesson import TemplatePlan, AddTemplatePlan, AddCustomPlan
from tools.permission_auth import permission_auth
from core.R2_client import R2_BUCKET,r2
from botocore.exceptions import ClientError

router = APIRouter(prefix="/plan", tags=["Plan"])
@router.get("/preset_planlist")
async def preset_planlist(
        db: Session = Depends(get_db),
):
    try:
        preset_plan = db.execute(select(TrainingPlan.plan_name.label('plan_name'),
                                        TrainingPlanLesson.lesson_order.label('order'),
                                        Lessons.lesson_name.label('lesson_name'))
                                 .select_from(TrainingPlan)
                                 .join(TrainingPlanLesson, TrainingPlanLesson.plan_id==TrainingPlan.id)
                                 .join(Lessons, Lessons.id==TrainingPlanLesson.lesson_id)
                                 ).all()
        return [{
            "plan_name":item.plan_name,
            "order":item.order,
            "lesson_name":item.lesson_name
        } for item in preset_plan]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create_preset_plan")
async def create_preset_plan(
        data:TemplatePlan,
        db: Session = Depends(get_db),
        existing_account: dict = Depends(permission_auth),
):
    if existing_account["role"] not in ["administer", "manager"]:
        raise HTTPException(status_code=400, detail="Unauthorized")
    try:
        new_template_plan = TrainingPlan(
            plan_name=data.plan_name,
            description=data.description,
            created_by=existing_account["account_id"]
        )
        db.add(new_template_plan)
        db.flush()
        for lesson_item in data.lesson_list:
            new_training_plan_lesson = TrainingPlanLesson(
                plan_id=new_template_plan.id,
                lesson_id=lesson_item.lesson_id,
                lesson_order=lesson_item.order,
            )
            db.add(new_training_plan_lesson)
        db.commit()
        return {
            "message":"Create Template_plan successfully",
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=403, detail="Create Template_plan Failed")

@router.post("/add_template_plan")
async def add_template_plan(
        data: AddTemplatePlan,
        db: Session = Depends(get_db),
        existing_account: dict = Depends(permission_auth),
):
    try:
        new_custom_plan = CustomedPlan(
            plan_name=data.plan_name,
            template_plan_id=data.plan_id,
            user_id=existing_account["user_id"],
            source_type='preset',
            status='not_started'
        )
        db.add(new_custom_plan)
        db.flush()

        template_lessons = db.scalars(
            select(TrainingPlanLesson)
            .where(TrainingPlanLesson.plan_id == data.plan_id)
            .order_by(TrainingPlanLesson.lesson_order)
        ).all()

        for item in template_lessons:
            db.add(
                PlanLesson(
                    plan_id=new_custom_plan.id,
                    lesson_id=item.lesson_id,
                    lesson_order=item.lesson_order,
                    completed=False
                )
            )
        db.commit()
        return {
            "message":"Add Template_plan successfully",
        }
    except IntegrityError as e:
        db.rollback()
        print("IntegrityError:", e)
        print("Original error:", e.orig)

        raise HTTPException(
            status_code=409,
            detail=str(e.orig)
        )

@router.post("/add_custom_plan")
async def add_custom_plan(
        data: AddCustomPlan,
        db: Session = Depends(get_db),
        existing_account: dict = Depends(permission_auth),
):
    try:
        new_custom_plan = CustomedPlan(
            plan_name=data.plan_name,
            user_id=existing_account["user_id"],
            source_type='manual',
            status='not_started'
        )
        db.add(new_custom_plan)
        db.flush()

        for lesson_item in data.lesson_list:
            new_plan_lesson = PlanLesson(
                plan_id=new_custom_plan.id,
                lesson_id=lesson_item.lesson_id,
                lesson_order=lesson_item.order,
                completed=False
            )
            db.add(new_plan_lesson)
        db.commit()
        return {
            "message":"Add Custom_plan successfully",
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Add Custom_plan Failed")



