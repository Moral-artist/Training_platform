from pydantic import BaseModel, EmailStr, Field
from enum import Enum

class LessonForm(BaseModel):
    system_id: int
    lesson_name: str
    description: str
    lesson_video_url: str

class UploadVideo(BaseModel):
    filename: str
    size: int
    content_type: str

class LessonItem(BaseModel):
    lesson_id: int
    order: int


class TemplatePlan(BaseModel):
    plan_name: str
    description: str
    lesson_list:list[LessonItem] = Field(default_factory=list)

class AddTemplatePlan(BaseModel):
    plan_id: int
    plan_name: str

class AddCustomPlan(BaseModel):
    plan_name: str
    lesson_list: list[LessonItem] = Field(default_factory=list)