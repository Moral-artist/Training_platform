import math
from datetime import datetime
from dependencies.csrf import verify_csrf
from fastapi import FastAPI, Depends, HTTPException, Response, APIRouter
from sqlalchemy.orm import Session
from data_model.core_database import get_db
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from data_model.data_model import Systems, SystemLesson, Lessons, Account, Roles
from schema.lesson import LessonForm, UploadVideo
from tools.permission_auth import permission_auth
from core.R2_client import r2, R2_BUCKET
import uuid
from pathlib import Path

router = APIRouter(prefix="/lessons_video", tags=["LessonsVideo"])

@router.post("/upload_token")
async def upload_token(
        uploadvideo: UploadVideo,
        existing_account: dict = Depends(permission_auth),
):
    if existing_account["role"] not in ["manager","administer"]:
        raise HTTPException(status_code=403, detail="You dont have permission to upload")

    allowed_types = {
        "video/mp4",
        "video/webm"
    }

    if uploadvideo.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video type"
        )

    suffix = Path(uploadvideo.filename).suffix.lower()

    object_key = (
        f"videos/lessons/"
        f"{uuid.uuid4().hex}{suffix}"
    )

    upload_url = r2.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": R2_BUCKET,
            "Key": object_key,
            "ContentType": uploadvideo.content_type
        },
        ExpiresIn=300
    )

    return {
        "upload_url": upload_url,
        "object_key": object_key,
        "expires_in": 300
    }
