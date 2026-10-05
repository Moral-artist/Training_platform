from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from core.R2_client import R2_BUCKET, r2
from data_model.core_database import get_db
from data_model.data_model import VideoAsset
from schema.lesson import UploadVideo
from service.video_limits import rate_limit
from tools.permission_auth import permission_auth, permission_read_auth


router = APIRouter(prefix="/lessons_video", tags=["LessonsVideo"])

# 300 MiB
MAX_VIDEO_SIZE = 300 * 1024 * 1024
ALLOWED_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
}


def require_video_manager(account: dict) -> None:
    if account["role"] not in {"manager", "administer"}:
        raise HTTPException(status_code=403, detail="No video permission")


def get_owned_asset(
    asset_id: UUID,
    db: Session,
    account: dict,
    lock: bool = False,
) -> VideoAsset:
    asset = db.scalar(select(VideoAsset).where(VideoAsset.id == asset_id).with_for_update()) if lock else db.get(VideoAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Video not found")

    if account["role"] != "administer" and asset.created_by != account["account_id"]:
        raise HTTPException(status_code=403, detail="No access to this video")

    return asset


@router.post("/upload_token")
async def upload_token(
    uploadvideo: UploadVideo,
    db: Session = Depends(get_db),
    account: dict = Depends(permission_auth),
):
    require_video_manager(account)

    await rate_limit(account["account_id"], "upload", 10, 600)
    suffix = Path(uploadvideo.filename).suffix.lower()
    if ALLOWED_TYPES.get(suffix) != uploadvideo.content_type:
        raise HTTPException(status_code=400, detail="Unsupported video type")

    if not 0 < uploadvideo.size <= MAX_VIDEO_SIZE:
        raise HTTPException(status_code=400, detail="Invalid video size")

    asset_id = uuid4()
    source_key = f"videos/source/{asset_id}{suffix}"

    asset = VideoAsset(
        id=asset_id,
        source_object_key=source_key,
        status="pending_upload",
        declared_size=uploadvideo.size,
        content_type=uploadvideo.content_type,
        created_by=account["account_id"],
    )
    db.add(asset)
    db.commit()

    try:
        upload_url = r2.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": R2_BUCKET,
                "Key": source_key,
                "ContentType": uploadvideo.content_type,
            },
            ExpiresIn=300,
        )
    except Exception:
        db.delete(asset)
        db.commit()
        raise HTTPException(status_code=502, detail="Cannot create upload URL")

    return {
        "asset_id": str(asset_id),
        "upload_url": upload_url,
        "expires_in": 300,
    }


@router.post("/{asset_id}/complete")
def complete_upload(
    asset_id: UUID,
    db: Session = Depends(get_db),
    account: dict = Depends(permission_auth),
):
    require_video_manager(account)
    asset = get_owned_asset(asset_id, db, account, lock=True)

    if asset.status in {"uploaded", "processing", "ready"}:
        return {"asset_id": str(asset.id), "status": asset.status}

    if asset.status != "pending_upload":
        raise HTTPException(status_code=409, detail="Invalid video status")

    try:
        obj = r2.head_object(
            Bucket=R2_BUCKET,
            Key=asset.source_object_key,
        )
    except ClientError:
        raise HTTPException(status_code=400, detail="Upload not found in R2")

    if not 0 < obj["ContentLength"] <= MAX_VIDEO_SIZE:
        raise HTTPException(status_code=400, detail="Invalid uploaded file size")

    if asset.declared_size is not None and obj["ContentLength"] != asset.declared_size:
        raise HTTPException(400, "Uploaded size does not match declared size")

    expected_type = ALLOWED_TYPES.get(Path(asset.source_object_key).suffix.lower())
    if obj.get("ContentType") != expected_type:
        raise HTTPException(status_code=400, detail="Invalid uploaded file type")

    asset.status = "uploaded"
    asset.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"asset_id": str(asset.id), "status": asset.status}


@router.get("/{asset_id}/status")
def video_status(
    asset_id: UUID,
    db: Session = Depends(get_db),
    account: dict = Depends(permission_read_auth),
):
    require_video_manager(account)
    asset = get_owned_asset(asset_id, db, account)

    return {
        "asset_id": str(asset.id),
        "status": asset.status,
        "error_message": "Video processing failed; contact administrator" if asset.status == "failed" else None,
        "duration_seconds": asset.duration_seconds,
    }


@router.post("/{asset_id}/retry")
def retry_transcode(asset_id: UUID, db: Session = Depends(get_db), account: dict = Depends(permission_auth)):
    require_video_manager(account)
    asset = get_owned_asset(asset_id, db, account, lock=True)
    if asset.status != "failed":
        raise HTTPException(409, "Only failed assets can be retried")
    asset.status = "uploaded"
    asset.error_message = None
    asset.processing_started_at = None
    asset.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"asset_id": str(asset.id), "status": asset.status}
