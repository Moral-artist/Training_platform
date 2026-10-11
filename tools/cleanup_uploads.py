"""清理超时未完成上传。默认 dry-run，--apply 才撤销分段和删除待上传记录。"""

import argparse
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from botocore.exceptions import ClientError
from data_model.core_database import SessionLocal
from data_model.data_model import VideoAsset, Lessons
from data_model.config import settings
from core.R2_client import r2, R2_BUCKET


def cleanup(apply=False):
    cutoff = datetime.now(timezone.utc) - timedelta(
        hours=settings.UPLOAD_RETENTION_HOURS
    )
    with SessionLocal() as db:
        rows = db.scalars(
            select(VideoAsset)
            .where(
                VideoAsset.status == "pending_upload", VideoAsset.updated_at < cutoff
            )
            .with_for_update(skip_locked=True)
        ).all()
        for asset in rows:
            if db.scalar(
                select(Lessons.id).where(Lessons.video_asset_id == asset.id).limit(1)
            ):
                continue
            print(f"expired pending asset={asset.id}")
            if not apply:
                continue
            if asset.multipart_upload_id:
                try:
                    r2.abort_multipart_upload(
                        Bucket=R2_BUCKET,
                        Key=asset.source_object_key,
                        UploadId=asset.multipart_upload_id,
                    )
                except ClientError as error:
                    if error.response.get("Error", {}).get("Code") != "NoSuchUpload":
                        raise
            r2.delete_object(Bucket=R2_BUCKET, Key=asset.source_object_key)
            db.delete(asset)
        if apply:
            db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    cleanup(parser.parse_args().apply)
