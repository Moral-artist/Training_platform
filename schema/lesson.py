from pydantic import BaseModel, EmailStr, Field
from enum import Enum

class LessonForm(BaseModel):
    system_id: int
    lesson_name: str
    description: str
    lesson_video_url: str
