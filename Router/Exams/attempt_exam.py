from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select,update,delete
from tools.permission_auth import permission_auth
from data_model.core_database import get_db
from schema.exam import AttemptExamForm
from data_model.data_model import (Exams, ExamAttempts, ExamQuestion,LessonExam,
                                   AttemptAnswers, Questions, Lessons, Options)

router = APIRouter(prefix='', tags=['Attempt Exam'])

