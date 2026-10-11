"""新管理接口的严格请求契约；禁止客户端直接修改创建者和权限。"""

from uuid import UUID
from pydantic import BaseModel, Field


class LessonUpdate(BaseModel):
    lesson_name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    system_id: int = Field(gt=0)
    video_asset_id: UUID
    revision: int = Field(ge=1)


class MultipartStart(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    size: int = Field(gt=0)
    content_type: str = Field(pattern=r"^video/(mp4|webm)$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
