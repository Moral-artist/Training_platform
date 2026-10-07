from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update, delete, func, false, and_
from tools.permission_auth import permission_auth
from data_model.core_database import get_db
from schema.exam import ExamForm, AttemptExamForm, SubmitExamForm
from data_model.data_model import (Exams, ExamAttempts, ExamQuestion,LessonExam,
                                   AttemptAnswers, Questions, Lessons, Options)
from datetime import datetime, timezone
router = APIRouter(prefix="/exams", tags=["Exams"])


MEMBERSHIP_LEVEL = {
    "free": 0,
    "basic": 1,
    "pro": 2,
    "enterprise": 3,
}

@router.post("/createExams")
async def create_exams(
        exam_data: ExamForm,
        existing_account: dict = Depends(permission_auth),
        db: Session = Depends(get_db)):
    if existing_account["role"] not in ["administer", "manager"]:
        raise HTTPException(status_code=400, detail="Unauthorized")
    try:
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
                    is_correct=option.is_correct
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

@router.get("/getExams")
async def get_exams(
        lesson_id: int,
        db: Session = Depends(get_db),
        existing_account: dict = Depends(permission_auth)
):
    if MEMBERSHIP_LEVEL[existing_account["membership_level"]]<MEMBERSHIP_LEVEL['basic']:
        raise HTTPException(status_code=400, detail="Unauthorized")
    rows = db.execute(
        select(
            Lessons.lesson_name.label("lesson_name"),
            Exams.id.label('exam_id'),
            Exams.exam_name.label('exam_name'),
            Questions.id.label('question_id'),
            Questions.question_type.label('question_type'),
            Questions.question_name.label('question_name'),
            Options.id.label('option_id'),
            Options.option_key.label('option_key'),
            Options.option.label('option_value')
        )
        .select_from(Lessons)
        .join(LessonExam, LessonExam.lesson_id == Lessons.id)
        .join(Exams, Exams.id == LessonExam.exam_id)
        .join(ExamQuestion, ExamQuestion.exam_id == Exams.id)
        .join(Questions, Questions.id == ExamQuestion.question_id)
        .outerjoin(Options, Options.q_id==Questions.id)
        .where(Lessons.id == lesson_id)
        .order_by(
            Exams.id,
            Questions.id,
            Options.id,
        )
    ).all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Exam not found"
        )

    exams = {}
    for row in rows:

        if row.exam_id not in exams:
            exams[row.exam_id] = {
                "exam_id": row.exam_id,
                "exam_name": row.exam_name,
                "lesson_name": row.lesson_name,
                "questions": {}
            }

        if row.question_id not in exams[row.exam_id]["questions"]:
            exams[row.exam_id]["questions"][row.question_id] = {
                "question_id": row.question_id,
                "question_type": row.question_type,
                "question_name": row.question_name,
                "options": []
            }

        if row.option_id is not None:
            exams[row.exam_id]["questions"][row.question_id]["options"].append({
                "option_id": row.option_id,
                "option_key": row.option_key,
                "option_value": row.option_value
            })

    result = []

    for exam in exams.values():
        exam["questions"] = list(exam["questions"].values())
        result.append(exam)

    return result

@router.post("/deleteExams")
async def delete_exams(
        exam_id: int,
        db: Session = Depends(get_db),
        existing_account: dict = Depends(permission_auth)
):
    if existing_account["role"] not in ["administer", "manager"]:
        raise HTTPException(status_code=400, detail="Unauthorized")

    exam = db.scalar(
        select(Exams)
        .where(Exams.id == exam_id)
    )

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found"
        )

    try:
        db.delete(exam)
        db.commit()

        return {
            "message": "Exam deleted successfully"
        }

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Delete exam failed"
        )

@router.post("/attemptExam")
async def attempt_exam(
        attempt_data: AttemptExamForm,
        db: Session = Depends(get_db),
        existing_account: dict = Depends(permission_auth)
):
    if MEMBERSHIP_LEVEL[existing_account["membership_level"]]<MEMBERSHIP_LEVEL['basic']:
        raise HTTPException(status_code=400, detail="Unauthorized")
    try:
        max_attempt_no = db.scalar(
            select(
                func.max(ExamAttempts.attempt_no)
            )
            .where(
                ExamAttempts.exam_id == attempt_data.exam_id,
                ExamAttempts.user_id == existing_account["user_id"]
            )
        )

        attempted_time = (max_attempt_no or 0) + 1

        new_exam_attempt = ExamAttempts(
            exam_id=attempt_data.exam_id,
            user_id=existing_account["user_id"],
            attempt_no=attempted_time,
        )

        db.add(new_exam_attempt)
        db.commit()
        db.refresh(new_exam_attempt)

        return {
            "attempt_id": new_exam_attempt.id,
            "exam_id": attempt_data.exam_id,
            "attempt_no": attempted_time,
            "message": "Exam attempt started successfully"
        }

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Start exam attempt failed"
        )

@router.post("/submitAttempt")
async def submit_attempt(
        attempt_data: SubmitExamForm,
        db: Session = Depends(get_db),
        existing_account: dict = Depends(permission_auth)
):
    if (
        MEMBERSHIP_LEVEL[existing_account["membership_level"]]
        < MEMBERSHIP_LEVEL["basic"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Unauthorized"
        )

    current_attempt = db.scalar(
        select(ExamAttempts)
        .where(
            ExamAttempts.id == attempt_data.attempt_id,
            ExamAttempts.user_id == existing_account["user_id"]
        )
    )

    if current_attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Attempt not found"
        )

    if current_attempt.submit_time is not None:
        raise HTTPException(
            status_code=409,
            detail="This attempt has already been submitted"
        )

    question_rows = db.execute(
        select(
            Questions.id.label("question_id"),
            Questions.question_type.label("question_type"),
            Questions.answer.label("reference_answer"),
            Options.option_key.label("option_key")
        )
        .select_from(ExamQuestion)
        .join(
            Questions,
            Questions.id == ExamQuestion.question_id
        )
        .outerjoin(
            Options,
            and_(
                Options.q_id == Questions.id,
                Options.is_correct.is_(True)
            )
        )
        .where(
            ExamQuestion.exam_id == current_attempt.exam_id
        )
        .order_by(Questions.id)
    ).all()

    if not question_rows:
        raise HTTPException(
            status_code=404,
            detail="Exam questions not found"
        )

    questions = {}

    for row in question_rows:

        if row.question_id not in questions:
            questions[row.question_id] = {
                "question_type": row.question_type,
                "answer": row.reference_answer,
                "correct_options": set()
            }

        if row.option_key is not None:
            questions[row.question_id]["correct_options"].add(
                row.option_key
            )

    submitted_answers = {
        item.q_id: item.answer
        for item in attempt_data.questions
    }

    invalid_question_ids = (
        set(submitted_answers.keys())
        - set(questions.keys())
    )

    if invalid_question_ids:
        raise HTTPException(
            status_code=400,
            detail="Invalid question submitted"
        )

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
                    is_correct = (
                        user_answer.strip()
                        in correct_options
                    )

            elif question_type == "multipleQuestions":

                if user_answer:

                    user_options = {
                        option.strip()
                        for option in user_answer.split(",")
                        if option.strip()
                    }

                    is_correct = (
                        user_options
                        == question_info["correct_options"]
                    )

            elif question_type == "shortAnswer":

                reference_answer = question_info["answer"]

                if (
                    user_answer is not None
                    and reference_answer is not None
                ):
                    is_correct = (
                        user_answer.strip().casefold()
                        ==
                        reference_answer.strip().casefold()
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
                is_correct=is_correct
            )

            db.add(new_answer)

        score_percent = (
            total_score / total_questions * 100
            if total_questions > 0
            else 0
        )

        passed = score_percent >= 60

        current_attempt.score = score_percent
        current_attempt.passed = passed
        current_attempt.submit_time = datetime.now(timezone.utc)

        db.commit()

        return {
            "attempt_id": current_attempt.id,
            "exam_id": current_attempt.exam_id,
            "total_questions": total_questions,
            "total_correct": total_correct,
            "score": score_percent,
            "passed": passed,
            "message": "Exam submitted successfully"
        }

    except Exception:
        db.rollback()
        raise


