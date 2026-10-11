"""清理未发布/旧版本 HLS。只清理超过保留期的目录，保留当前版本及所有处理中资产。"""

import argparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from sqlalchemy import select
from data_model.core_database import SessionLocal
from data_model.data_model import VideoAsset
from core.R2_client import r2, R2_BUCKET


def cleanup(days=7, apply=False):
    if days < 1:
        raise ValueError("Retention must be at least one day")
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with SessionLocal() as db:
        assets = db.scalars(select(VideoAsset)).all()
        active = {
            str(a.id)
            for a in assets
            if a.status in {"pending_upload", "uploaded", "processing"}
        }
        published = {
            a.master_playlist_key.rsplit("/", 1)[0] + "/"
            for a in assets
            if a.master_playlist_key
        }
    versions = defaultdict(list)
    for page in r2.get_paginator("list_objects_v2").paginate(
        Bucket=R2_BUCKET, Prefix="videos/hls/"
    ):
        for obj in page.get("Contents", []):
            parts = obj["Key"].split("/")
            if len(parts) < 5:
                continue
            prefix = "/".join(parts[:4]) + "/"
            versions[prefix].append(obj)
    for prefix, objects in versions.items():
        if (
            prefix in published
            or prefix.split("/")[2] in active
            or any(o["LastModified"] >= cutoff for o in objects)
        ):
            continue
        print(
            f'unpublished HLS version={prefix} objects={len(objects)} bytes={sum(o["Size"] for o in objects)}'
        )
        if not apply:
            continue
        for offset in range(0, len(objects), 1000):
            result = r2.delete_objects(
                Bucket=R2_BUCKET,
                Delete={
                    "Objects": [
                        {"Key": o["Key"]} for o in objects[offset : offset + 1000]
                    ],
                    "Quiet": True,
                },
            )
            if result.get("Errors"):
                raise RuntimeError("Some HLS objects could not be removed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    cleanup(args.days, args.apply)
