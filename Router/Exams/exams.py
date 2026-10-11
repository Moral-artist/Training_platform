from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update, delete, func, false, and_
from tools.permission_auth import permission_auth, permission_read_auth
from service.lesson_access import require_lesson_access, can_manage_lesson
from data_model.core_database import get_db
from schema.exam import ExamForm, AttemptExamForm, SubmitExamForm
from data_model.data_model import (
    Exams,
    ExamAttempts,
    ExamQuestion,
    LessonExam,
    AttemptAnswers,
    Questions,
    Lessons,
    Options,
    PlanLesson,
    Account,
    CustomedPlan
)
from datetime import datetime, timezone

router = APIRouter(prefix="/exams", tags=["Exams"])


# 考试访问由会话和课程授权决定；创建/删除仍校验管理角色与课程维护权。
@router.post("/createExams")
async def create_exams(
    exam_data: ExamForm,
    existing_account: dict = Depends(permission_auth),
    db: Session = Depends(get_db),
):
    if existing_account["role"] not in ["administer", "manager"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    lesson = require_lesson_access(db, existing_account, exam_data.lesson_id)
    if not can_manage_lesson(db, existing_account, lesson):
        raise HTTPException(403, "No course management permission")
    try:
        db.scalar(
            select(Lessons.id)
            .where(Lessons.id == exam_data.lesson_id)
            .with_for_update()
        )

        existing_exam_id = db.scalar(
            select(Exams.id)
            .join(LessonExam, LessonExam.exam_id == Exams.id)
            .where(
                LessonExam.lesson_id == exam_data.lesson_id,
                Exams.deleted_at.is_(None)
            )
            .limit(1)
        )

        if existing_exam_id is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Exam already exists: {existing_exam_id}. Please edit it."
            )

        new_exam = Exams(
            exam_name=exam_data.exam_name,
        )
        db.add(new_exam)
        db.flush()

        for question in exam_data.questions:
            new_question = Questions(
                question_name=question.question_name,
                question_type=question.question_type.value,
                answer=question.answer,
            )
            db.add(new_question)
            db.flush()
            for option in question.options:
                new_option = Options(
                    q_id=new_question.id,
                    option_key=option.option_key,
                    option=option.option_value,
                    is_correct=option.is_correct,
                )
                db.add(new_option)

            new_exam_question = ExamQuestion(
                exam_id=new_exam.id,
                question_id=new_question.id,
            )
            db.add(new_exam_question)
        new_lesson_exam = LessonExam(
            exam_id=new_exam.id,
            lesson_id=exam_data.lesson_id,
        )
        db.add(new_lesson_exam)
        db.commit()

        return {
            "lesson_id": new_lesson_exam.lesson_id,
            "exam_id": new_exam.id,
            "message": "Exams created successfully",
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Create Exam failed")

@router.put("/updateExams/{exam_id}")
def update_exams(
    exam_id: int,
    exam_data: ExamForm,
    db: Session = Depends(get_db),
    account: dict = Depends(permission_auth),
):
    if account["role"] not in ["administer", "manager"]:
        raise HTTPException(403, "Unauthorized")

    lesson = db.get(Lessons, exam_data.lesson_id)

    if lesson is None or lesson.deleted_at is not None:
        raise HTTPException(404, "Lesson not found")

    if not can_manage_lesson(db, account, lesson):
        raise HTTPException(
            403, "No course management permission"
        )

    # 锁定当前试卷
    exam = db.scalar(
        select(Exams)
        .where(Exams.id == exam_id)
        .with_for_update()
    )

    if exam is None or exam.deleted_at is not None:
        raise HTTPException(404, "Exam not found")

    # 校验试卷确实属于当前课程
    related_lessons = db.scalars(
        select(LessonExam.lesson_id)
        .where(LessonExam.exam_id == exam_id)
    ).all()

    if exam_data.lesson_id not in related_lessons:
        raise HTTPException(
            404, "Exam does not belong to lesson"
        )

    # 如果试卷被多个课程共用，禁止直接整体修改
    if len(related_lessons) != 1:
        raise HTTPException(
            409, "Shared exam cannot be edited directly"
        )

    # 有考试记录时不允许替换题目
    has_attempt = db.scalar(
        select(ExamAttempts.id)
        .where(ExamAttempts.exam_id == exam_id)
        .limit(1)
    )

    if has_attempt is not None:
        raise HTTPException(
            409,
            "Exam has attempts; question editing requires versioning"
        )

    try:
        exam.exam_name = exam_data.exam_name

        # 记录旧题目，用于后续清理
        old_question_ids = db.scalars(
            select(ExamQuestion.question_id)
            .where(ExamQuestion.exam_id == exam_id)
        ).all()

        # 清除原有的试卷与题目关联
        db.execute(
            delete(ExamQuestion)
            .where(ExamQuestion.exam_id == exam_id)
        )

        # 根据提交的表单创建新的题目
        for question in exam_data.questions:
            new_question = Questions(
                question_name=question.question_name,
                question_type=question.question_type.value,
                answer=question.answer,
            )

            db.add(new_question)
            db.flush()

            for option in question.options:
                db.add(
                    Options(
                        q_id=new_question.id,
                        option_key=option.option_key,
                        option=option.option_value,
                        is_correct=option.is_correct
                    )
                )

            db.add(
                ExamQuestion(
                    exam_id=exam_id,
                    question_id=new_question.id
                )
            )

        db.flush()

        # 清理不再被引用的旧题目
        for question_id in old_question_ids:

            still_used = db.scalar(
                select(ExamQuestion.question_id)
                .where(
                    ExamQuestion.question_id == question_id
                )
                .limit(1)
            )

            has_answers = db.scalar(
                select(AttemptAnswers.question_id)
                .where(
                    AttemptAnswers.question_id == question_id
                )
                .limit(1)
            )

            if still_used is None and has_answers is None:
                db.execute(
                    delete(Options)
                    .where(Options.q_id == question_id)
                )

                db.execute(
                    delete(Questions)
                    .where(Questions.id == question_id)
                )

        db.commit()

        return {
            "exam_id": exam_id,
            "lesson_id": exam_data.lesson_id,
            "message": "Exam updated successfully"
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "Update exam failed"
        )
    except Exception:
        db.rollback()
        raise

@router.get("/manageExams")
def manage_exams(
    lesson_id: int,
    db: Session = Depends(get_db),
    account: dict = Depends(permission_read_auth),
):
    if account["role"] not in ["administer", "manager"]:
        raise HTTPException(403, "Unauthorized")

    lesson = db.get(Lessons, lesson_id)

    if lesson is None or lesson.deleted_at is not None:
        raise HTTPException(404, "Lesson not found")

    if not can_manage_lesson(db, account, lesson):
        raise HTTPException(403, "No course management permission")

    existing_exams = db.scalars(
        select(Exams)
        .join(LessonExam, LessonExam.exam_id == Exams.id)
        .where(
            LessonExam.lesson_id == lesson_id,
            Exams.deleted_at.is_(None)
        )
        .order_by(Exams.id)
    ).all()

    result = []

    for exam in existing_exams:
        question_ids = db.scalars(
            select(ExamQuestion.question_id)
            .where(ExamQuestion.exam_id == exam.id)
            .order_by(ExamQuestion.question_id)
        ).all()

        question_list = []

        for question_id in question_ids:
            question = db.get(Questions, question_id)

            options = db.scalars(
                select(Options)
                .where(Options.q_id == question_id)
                .order_by(Options.id)
            ).all()

            question_list.append({
                "question_id": question.id,
                "question_name": question.question_name,
                "question_type": question.question_type,
                "answer": question.answer,
                "options": [
                    {
                        "option_id": option.id,
                        "option_key": option.option_key,
                        "option_value": option.option,
                        "is_correct": option.is_correct
                    }
                    for option in options
                ]
            })

        result.append({
            "exam_id": exam.id,
            "exam_name": exam.exam_name,
            "lesson_id": lesson_id,
            "questions": question_list
        })

    return result

@router.get("/getExams")
async def get_exams(
    lesson_id: int,
    db: Session = Depends(get_db),
    existing_account: dict = Depends(permission_read_auth),
):
    require_lesson_access(db, existing_account, lesson_id)
    rows = db.execute(
        select(
            Lessons.lesson_name.label("lesson_name"),
            Exams.id.label("exam_id"),
            Exams.exam_name.label("exam_name"),
            Questions.id.label("question_id"),
            Questions.question_type.label("question_type"),
            Questions.question_name.label("question_name"),
            Options.id.label("option_id"),
            Options.option_key.label("option_key"),
            Options.option.label("option_value"),
        )
        .select_from(Lessons)
        .join(LessonExam, LessonExam.lesson_id == Lessons.id)
        .join(Exams, Exams.id == LessonExam.exam_id)
        .join(ExamQuestion, ExamQuestion.exam_id == Exams.id)
        .join(Questions, Questions.id == ExamQuestion.question_id)
        .outerjoin(Options, Options.q_id == Questions.id)
        .where(Lessons.id == lesson_id, Exams.deleted_at.is_(None))
        .order_by(
            Exams.id,
            Questions.id,
            Options.id,
        )
    ).all()

    if not rows:
        raise HTTPException(status_code=404, detail="Exam not found")

    exams = {}
    for row in rows:

        if row.exam_id not in exams:
            exams[row.exam_id] = {
                "exam_id": row.exam_id,
                "exam_name": row.exam_name,
                "lesson_name": row.lesson_name,
                "questions": {},
            }

        if row.question_id not in exams[row.exam_id]["questions"]:
            exams[row.exam_id]["questions"][row.question_id] = {
                "question_id": row.question_id,
                "question_type": row.question_type,
                "question_name": row.question_name,
                "options": [],
            }

        if row.option_id is not None:
            exams[row.exam_id]["questions"][row.question_id]["options"].append(
                {
                    "option_id": row.option_id,
                    "option_key": row.option_key,
                    "option_value": row.option_value,
                }
            )

    result = []

    for exam in exams.values():
        exam["questions"] = list(exam["questions"].values())
        result.append(exam)

    return result


@router.post("/deleteExams")
async def delete_exams(
    exam_id: int,
    db: Session = Depends(get_db),
    existing_account: dict = Depends(permission_auth),
):
    if existing_account["role"] not in ["administer", "manager"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    exam = db.scalar(select(Exams).where(Exams.id == exam_id))

    if exam is None or exam.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Exam not found")

    associated = db.scalars(
        select(LessonExam.lesson_id).where(LessonExam.exam_id == exam_id)
    ).all()
    if not associated or not all(
        can_manage_lesson(db, existing_account, db.get(Lessons, lid))
        for lid in associated
    ):
        raise HTTPException(403, "No course management permission")
    try:
        exam.deleted_at = datetime.now(timezone.utc)
        db.commit()

        return {"message": "Exam deleted successfully"}

    except IntegrityError:
        db.rollback()

        raise HTTPException(status_code=400, detail="Delete exam failed")



@router.post("/attemptExam")
def attempt_exam(
    attempt_data: AttemptExamForm,
    db: Session = Depends(get_db),
    account: dict = Depends(permission_auth),
):
    user_id = account["user_id"]
    plan_id = attempt_data.plan_id
    lesson_id = attempt_data.lesson_id
    exam_id = attempt_data.exam_id

    # 1. 确认用户有课程访问权限
    require_lesson_access(db, account, lesson_id)

    # 2. 确认试卷属于该课程
    if not db.get(LessonExam, (lesson_id, exam_id)):
        raise HTTPException(
            status_code=404,
            detail="Exam does not belong to lesson"
        )

    # 3. 确认试卷未被删除
    exam = db.get(Exams, exam_id)

    if exam is None or exam.deleted_at is not None:
        raise HTTPException(404, "Exam not found")

    # 4. 如果从培训计划进入，验证归属关系
    if plan_id is not None:
        plan = db.scalar(
            select(CustomedPlan)
            .where(
                CustomedPlan.id == plan_id,
                CustomedPlan.user_id == user_id
            )
        )

        if plan is None:
            raise HTTPException(
                404, "Training plan not found"
            )

        plan_lesson = db.get(
            PlanLesson,
            (lesson_id, plan_id)
        )

        if plan_lesson is None:
            raise HTTPException(
                403, "Lesson does not belong to plan"
            )

    try:
        db.scalar(
            select(Account)
            .where(Account.id == account["account_id"])
            .with_for_update()
        )

        context = [
            ExamAttempts.exam_id == exam_id,
            ExamAttempts.user_id == user_id,
            ExamAttempts.lesson_id == lesson_id,
        ]

        if plan_id is None:
            context.append(ExamAttempts.plan_id.is_(None))
        else:
            context.append(ExamAttempts.plan_id == plan_id)

        unfinished = db.scalar(
            select(ExamAttempts)
            .where(
                *context,
                ExamAttempts.submit_time.is_(None)
            )
            .order_by(ExamAttempts.id.desc())
        )

        if unfinished is not None:
            return {
                "attempt_id": unfinished.id,
                "exam_id": exam_id,
                "attempt_no": unfinished.attempt_no
            }

        # 8. 计算当前计划、课程、试卷中的考试次数
        max_no = db.scalar(
            select(func.max(ExamAttempts.attempt_no))
            .where(*context)
        )

        next_no = (max_no or 0) + 1

        # 9. 创建考试记录
        new_attempt = ExamAttempts(
            exam_id=exam_id,
            lesson_id=lesson_id,
            plan_id=plan_id,
            user_id=user_id,
            attempt_no=next_no,
        )

        db.add(new_attempt)
        db.commit()
        db.refresh(new_attempt)

        return {
            "attempt_id": new_attempt.id,
            "exam_id": exam_id,
            "attempt_no": next_no,
            "message": "Exam attempt started successfully"
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "Start exam attempt failed"
        )

@router.post("/submitAttempt")
async def submit_attempt(
    attempt_data: SubmitExamForm,
    db: Session = Depends(get_db),
    existing_account: dict = Depends(permission_auth),
):

    current_attempt = db.scalar(
        select(ExamAttempts)
        .where(
            ExamAttempts.id == attempt_data.attempt_id,
            ExamAttempts.user_id == existing_account["user_id"],
        )
        .with_for_update()
    )

    if current_attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found")

    exam = db.get(Exams, current_attempt.exam_id)
    if not exam or exam.deleted_at is not None:
        raise HTTPException(404, "Exam not found")
    lesson_id = current_attempt.lesson_id

    if not db.get(
            LessonExam,
            (lesson_id, current_attempt.exam_id)
    ):
        raise HTTPException(
            404, "Exam does not belong to lesson"
        )

    require_lesson_access(
        db,
        existing_account,
        lesson_id
    )
    if current_attempt.submit_time is not None:
        return {
            "attempt_id": current_attempt.id,
            "exam_id": current_attempt.exam_id,
            "score": current_attempt.score,
            "passed": current_attempt.passed,
        }

    question_rows = db.execute(
        select(
            Questions.id.label("question_id"),
            Questions.question_type.label("question_type"),
            Questions.answer.label("reference_answer"),
            Options.option_key.label("option_key"),
        )
        .select_from(ExamQuestion)
        .join(Questions, Questions.id == ExamQuestion.question_id)
        .outerjoin(
            Options, and_(Options.q_id == Questions.id, Options.is_correct.is_(True))
        )
        .where(ExamQuestion.exam_id == current_attempt.exam_id)
        .order_by(Questions.id)
    ).all()

    if not question_rows:
        raise HTTPException(status_code=404, detail="Exam questions not found")

    questions = {}

    for row in question_rows:

        if row.question_id not in questions:
            questions[row.question_id] = {
                "question_type": row.question_type,
                "answer": row.reference_answer,
                "correct_options": set(),
            }

        if row.option_key is not None:
            questions[row.question_id]["correct_options"].add(row.option_key)

    submitted_answers = {item.q_id: item.answer for item in attempt_data.questions}

    invalid_question_ids = set(submitted_answers.keys()) - set(questions.keys())

    if invalid_question_ids:
        raise HTTPException(status_code=400, detail="Invalid question submitted")

    total_score = 0
    total_questions = len(questions)
    total_correct = 0

    try:

        for question_id, question_info in questions.items():

            user_answer = submitted_answers.get(question_id)

            question_type = question_info["question_type"]

            is_correct = False

            if question_type == "singleQuestion":

                correct_options = question_info["correct_options"]

                if user_answer is not None:
                    is_correct = user_answer.strip() in correct_options

            elif question_type == "multipleQuestions":

                if user_answer:

                    user_options = {
                        option.strip()
                        for option in user_answer.split(",")
                        if option.strip()
                    }

                    is_correct = user_options == question_info["correct_options"]

            elif question_type == "shortAnswer":

                reference_answer = question_info["answer"]

                if user_answer is not None and reference_answer is not None:
                    is_correct = (
                        user_answer.strip().casefold()
                        == reference_answer.strip().casefold()
                    )

            score = 1 if is_correct else 0

            if is_correct:
                total_correct += 1
                total_score += score

            new_answer = AttemptAnswers(
                attempt_id=current_attempt.id,
                question_id=question_id,
                answer=user_answer or "",
                score=score,
                is_correct=is_correct,
            )

            db.add(new_answer)

        score_percent = (
            total_score / total_questions * 100 if total_questions > 0 else 0
        )

        passed = score_percent >= 60

        now = datetime.now(timezone.utc)

        current_attempt.score = score_percent
        current_attempt.passed = passed
        current_attempt.submit_time = now

        if current_attempt.plan_id is not None:

            plan = db.scalar(
                select(CustomedPlan)
                .where(
                    CustomedPlan.id == current_attempt.plan_id,
                    CustomedPlan.user_id == existing_account["user_id"]
                )
                .with_for_update()
            )

            if plan is None:
                raise HTTPException(
                    404, "Training plan not found"
                )

            plan_lesson = db.scalar(
                select(PlanLesson)
                .where(
                    PlanLesson.plan_id == current_attempt.plan_id,
                    PlanLesson.lesson_id == current_attempt.lesson_id
                )
                .with_for_update()
            )

            if plan_lesson is None:
                raise HTTPException(
                    404, "Plan lesson not found"
                )

            # 通过考试才标记完成
            if passed and not plan_lesson.completed:
                plan_lesson.completed = True
                plan_lesson.completed_at = now

            # 统计当前计划的课程完成数量
            db.flush()

            total, completed = db.execute(
                select(
                    func.count(PlanLesson.lesson_id),
                    func.count(PlanLesson.lesson_id)
                    .filter(PlanLesson.completed.is_(True))
                )
                .where(PlanLesson.plan_id == plan.id)
            ).one()

            if total > 0 and completed == total:
                plan.status = "completed"

            elif completed > 0:
                plan.status = "in_progress"

            elif plan.status == "not_started":
                plan.status = "in_progress"

        # 考试成绩、课程完成状态和计划状态一起提交
        db.commit()

        return {
            "attempt_id": current_attempt.id,
            "exam_id": current_attempt.exam_id,
            "total_questions": total_questions,
            "total_correct": total_correct,
            "score": score_percent,
            "passed": passed,
            "message": "Exam submitted successfully",
        }

    except Exception:
        db.rollback()
        raise


@router.get("/my_attempts")
def my_attempts(db: Session = Depends(get_db), account=Depends(permission_read_auth)):
    rows = db.scalars(
        select(ExamAttempts)
        .where(ExamAttempts.user_id == account["user_id"])
        .order_by(ExamAttempts.id.desc())
    ).all()
    return [
        {
            "attempt_id": i.id,
            "exam_id": i.exam_id,
            "attempt_no": i.attempt_no,
            "score": i.score if i.submit_time else None,
            "passed": i.passed if i.submit_time else None,
            "submitted": i.submit_time is not None,
        }
        for i in rows
    ]
