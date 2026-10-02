from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from uuid import UUID

class LessonForm(BaseModel):
    system_id: int = Field(gt=0)
    lesson_name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    video_asset_id: UUID

class UploadVideo(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    size: int = Field(gt=0, le=300 * 1024 * 1024)
    content_type: str = Field(pattern=r"^video/(mp4|webm)$")

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