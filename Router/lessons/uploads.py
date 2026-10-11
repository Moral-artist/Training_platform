"""R2 multipart lifecycle. 客户端仅持有短期分段签名；状态始终存储在数据库/R2。"""

import math
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError
from data_model.core_database import get_db
from data_model.data_model import VideoAsset, Lessons
from data_model.config import settings
from core.R2_client import r2, R2_BUCKET
from tools.permission_auth import permission_auth, permission_read_auth
from schema.course_management import MultipartStart
from Router.lessons.lesson_video import (
    get_owned_asset,
    require_video_manager,
    ALLOWED_TYPES,
)
from service.video_limits import rate_limit

router = APIRouter(prefix="/uploads", tags=["resumable uploads"])


def validate_part_size():
    if not 5 * 1024 * 1024 <= settings.UPLOAD_PART_BYTES <= 128 * 1024 * 1024:
        raise HTTPException(503, "Upload part size misconfigured")


def list_parts(asset):
    parts, marker = [], 0
    while True:
        result = r2.list_parts(
            Bucket=R2_BUCKET,
            Key=asset.source_object_key,
            UploadId=asset.multipart_upload_id,
            PartNumberMarker=marker,
        )
        parts.extend(result.get("Parts", []))
        if not result.get("IsTruncated"):
            break
        marker = result["NextPartNumberMarker"]
    return parts


def upload_info(asset):
    # 从 R2 列出分段，浏览器丢失状态也能恢复。绝不把对象 Key/UploadId 回传。
    parts = []
    if asset.status == "pending_upload" and asset.multipart_upload_id:
        try:
            parts = list_parts(asset)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") == "NoSuchUpload":
                raise HTTPException(409, "Upload expired; discard and restart")
            raise HTTPException(502, "Upload storage unavailable")
    return {
        "asset_id": str(asset.id),
        "status": asset.status,
        "size": asset.declared_size,
        "content_hash": asset.content_hash,
        "part_size": asset.upload_part_size or settings.UPLOAD_PART_BYTES,
        "part_count": math.ceil(
            asset.declared_size / (asset.upload_part_size or settings.UPLOAD_PART_BYTES)
        ),
        "parts": [{"part_number": p["PartNumber"], "size": p["Size"]} for p in parts],
        "reused": asset.status != "pending_upload",
    }


@router.post("/start")
async def start_upload(
    data: MultipartStart,
    db: Session = Depends(get_db),
    account=Depends(permission_auth),
):
    require_video_manager(account)
    validate_part_size()
    if data.size > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(422, "File exceeds configured upload limit")
    suffix = Path(data.filename).suffix.lower()
    if ALLOWED_TYPES.get(suffix) != data.content_type:
        raise HTTPException(400, "Unsupported video type")
    existing = db.scalar(
        select(VideoAsset).where(
            VideoAsset.created_by == account["account_id"],
            VideoAsset.content_hash == data.content_hash,
        )
    )
    if existing:
        if (
            existing.declared_size != data.size
            or existing.content_type != data.content_type
        ):
            raise HTTPException(409, "Fingerprint metadata conflict")
        return upload_info(existing)
    await rate_limit(account["account_id"], "multipart", 20, 600)
    aid = uuid4()
    key = f"videos/source/{aid}{suffix}"
    upload = r2.create_multipart_upload(
        Bucket=R2_BUCKET, Key=key, ContentType=data.content_type
    )
    asset = VideoAsset(
        id=aid,
        source_object_key=key,
        status="pending_upload",
        declared_size=data.size,
        content_type=data.content_type,
        content_hash=data.content_hash,
        multipart_upload_id=upload["UploadId"],
        upload_part_size=settings.UPLOAD_PART_BYTES,
        created_by=account["account_id"],
    )
    db.add(asset)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # 并发相同文件仅保留一个任务，撤销输掉唯一约束竞争的 multipart。
        r2.abort_multipart_upload(
            Bucket=R2_BUCKET, Key=key, UploadId=upload["UploadId"]
        )
        existing = db.scalar(
            select(VideoAsset).where(
                VideoAsset.created_by == account["account_id"],
                VideoAsset.content_hash == data.content_hash,
            )
        )
        if not existing:
            raise HTTPException(409, "Upload creation conflict")
        return upload_info(existing)
    return upload_info(asset)


@router.get("/config")
def upload_config(account=Depends(permission_read_auth)):
    validate_part_size()
    return {
        "max_upload_bytes": settings.MAX_UPLOAD_BYTES,
        "part_size": settings.UPLOAD_PART_BYTES,
        "allowed_types": list(ALLOWED_TYPES.values()),
    }


@router.get("/{asset_id}")
def get_upload(
    asset_id: UUID, db: Session = Depends(get_db), account=Depends(permission_read_auth)
):
    validate_part_size()
    return upload_info(get_owned_asset(asset_id, db, account))


@router.post("/{asset_id}/part")
def sign_part(
    asset_id: UUID,
    part_number: int = Query(..., ge=1, le=10000),
    db: Session = Depends(get_db),
    account=Depends(permission_auth),
):
    validate_part_size()
    asset = get_owned_asset(asset_id, db, account, True)
    if asset.status != "pending_upload" or not asset.multipart_upload_id:
        raise HTTPException(409, "Upload is not pending")
    if part_number > math.ceil(
        asset.declared_size / (asset.upload_part_size or settings.UPLOAD_PART_BYTES)
    ):
        raise HTTPException(422, "Invalid part number")
    url = r2.generate_presigned_url(
        "upload_part",
        Params={
            "Bucket": R2_BUCKET,
            "Key": asset.source_object_key,
            "UploadId": asset.multipart_upload_id,
            "PartNumber": part_number,
        },
        ExpiresIn=900,
    )
    asset.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"upload_url": url, "expires_in": 900}


@router.post("/{asset_id}/complete")
def complete(
    asset_id: UUID, db: Session = Depends(get_db), account=Depends(permission_auth)
):
    validate_part_size()
    asset = get_owned_asset(asset_id, db, account, True)
    if asset.status in {"uploaded", "processing", "ready"}:
        return {"asset_id": str(asset.id), "status": asset.status}
    if asset.status != "pending_upload" or not asset.multipart_upload_id:
        raise HTTPException(409, "Upload cannot be completed")
    # R2 complete 成功、数据库提交前进程崩溃时，HEAD 可将任务恢复到 uploaded。
    try:
        metadata = r2.head_object(Bucket=R2_BUCKET, Key=asset.source_object_key)
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") not in {
            "404",
            "NoSuchKey",
            "NotFound",
        }:
            raise HTTPException(502, "Upload storage unavailable")
        metadata = None
    if metadata is None:
        parts = list_parts(asset)
        count = math.ceil(
            asset.declared_size / (asset.upload_part_size or settings.UPLOAD_PART_BYTES)
        )
        if len(parts) != count:
            raise HTTPException(409, "Upload parts incomplete")
        for number, part in enumerate(parts, 1):
            expected = min(
                asset.upload_part_size or settings.UPLOAD_PART_BYTES,
                asset.declared_size
                - (number - 1) * (asset.upload_part_size or settings.UPLOAD_PART_BYTES),
            )
            if part["PartNumber"] != number or part["Size"] != expected:
                raise HTTPException(422, "Upload part size mismatch")
        r2.complete_multipart_upload(
            Bucket=R2_BUCKET,
            Key=asset.source_object_key,
            UploadId=asset.multipart_upload_id,
            MultipartUpload={
                "Parts": [
                    {"PartNumber": p["PartNumber"], "ETag": p["ETag"]} for p in parts
                ]
            },
        )
        metadata = r2.head_object(Bucket=R2_BUCKET, Key=asset.source_object_key)
    if (
        metadata["ContentLength"] != asset.declared_size
        or metadata.get("ContentType") != asset.content_type
    ):
        raise HTTPException(422, "Uploaded object metadata mismatch")
    asset.status = "uploaded"
    asset.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"asset_id": str(asset.id), "status": asset.status}


@router.delete("/{asset_id}")
def discard(
    asset_id: UUID, db: Session = Depends(get_db), account=Depends(permission_auth)
):
    asset = get_owned_asset(asset_id, db, account, True)
    if asset.status != "pending_upload" or db.scalar(
        select(Lessons.id).where(Lessons.video_asset_id == asset.id).limit(1)
    ):
        raise HTTPException(409, "Only unbound pending uploads can be discarded")
    if asset.multipart_upload_id:
        try:
            r2.abort_multipart_upload(
                Bucket=R2_BUCKET,
                Key=asset.source_object_key,
                UploadId=asset.multipart_upload_id,
            )
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") != "NoSuchUpload":
                raise HTTPException(502, "Cannot discard upload")
    # complete 成功但 DB 尚未提交的源对象也需清理。
    r2.delete_object(Bucket=R2_BUCKET, Key=asset.source_object_key)
    db.delete(asset)
    db.commit()
    return {"message": "Pending upload discarded"}
