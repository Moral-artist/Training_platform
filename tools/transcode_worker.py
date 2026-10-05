"""独立运行 python -m tools.transcode_worker；不在 FastAPI 请求内转码。"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import subprocess
import tempfile
import time
from uuid import UUID, uuid4

from sqlalchemy import select
from data_model.core_database import SessionLocal
from data_model.data_model import VideoAsset
from data_model.config import settings
from core.R2_client import R2_BUCKET, r2

log = logging.getLogger("transcode")


def run_media_command(args: list[str], timeout: int) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    return result.stdout


def transcode_source(source: Path, output: Path) -> float:
    """生成 360p/720p（不超过源高度）、H264/AAC、4 秒 TS 分片。支持无音轨。"""
    probe = json.loads(run_media_command([
        settings.FFPROBE_PATH, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(source)
    ], 60))
    video = next((s for s in probe["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        raise ValueError("No video stream")
    height = int(video["height"])
    levels = [h for h in (360, 720) if h <= height]
    if not levels:
        levels = [max(2, height // 2 * 2)]
    master = ["#EXTM3U", "#EXT-X-VERSION:3", "#EXT-X-INDEPENDENT-SEGMENTS"]
    for h in levels:
        folder = output / f"{h}p"
        folder.mkdir(parents=True, exist_ok=True)
        bitrate = "800k" if h <= 360 else "2500k"
        bandwidth = 1200000 if h <= 360 else 3500000
        run_media_command([
            settings.FFMPEG_PATH, "-nostdin", "-y", "-v", "error", "-i", str(source),
            "-map", "0:v:0", "-map", "0:a:0?", "-vf", f"scale=-2:{h},setsar=1",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-b:v", bitrate,
            "-maxrate", bitrate, "-bufsize", "5000k", "-flags", "+cgop", "-sc_threshold", "0",
            "-force_key_frames", "expr:gte(t,n_forced*4)",
            "-c:a", "aac", "-b:a", "128k", "-ac", "2",
            "-f", "hls", "-hls_time", "4", "-hls_playlist_type", "vod", "-hls_list_size", "0",
            "-hls_flags", "independent_segments",
            "-hls_segment_filename", str(folder / "segment_%05d.ts"), str(folder / "index.m3u8"),
        ], settings.TRANSCODE_TIMEOUT_SECONDS)
        master += [f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth}", f"{h}p/index.m3u8"]
    (output / "master.m3u8").write_text("\n".join(master) + "\n")
    return float(probe["format"].get("duration", 0))


def claim_asset():
    """行锁避免两个转码进程领取同一任务；不持有长事务。"""
    with SessionLocal() as db:
        asset = db.scalar(select(VideoAsset).where(VideoAsset.status == "uploaded")
                          .order_by(VideoAsset.created_at).with_for_update(skip_locked=True).limit(1))
        if asset is None:
            return None
        attempt_id = datetime.now(timezone.utc)
        asset.status = "processing"
        asset.processing_started_at = attempt_id
        asset.updated_at = attempt_id
        asset.attempt_count += 1
        db.commit()
        return asset.id, asset.source_object_key, asset.attempt_count


def process_asset(job):
    asset_id, source_key, attempt_number = job
    # 新版本目录保证重试和旧 Token 不会混用文件。
    prefix = f"videos/hls/{asset_id}/{uuid4()}/"
    try:
        with tempfile.TemporaryDirectory(prefix="training-hls-") as tmp:
            root = Path(tmp)
            source = root / ("source" + Path(source_key).suffix)
            metadata = r2.head_object(Bucket=R2_BUCKET, Key=source_key)
            if not 0 < metadata["ContentLength"] <= 300 * 1024 * 1024:
                raise ValueError("Source size exceeds allowed size")
            r2.download_file(R2_BUCKET, source_key, str(source))
            if not 0 < source.stat().st_size <= 300 * 1024 * 1024:
                raise ValueError("Downloaded source size invalid")
            out = root / "hls"
            out.mkdir()
            duration = transcode_source(source, out)
            files = sorted(out.rglob("*"), key=lambda p: p.name == "master.m3u8")
            for file in files:
                if not file.is_file():
                    continue
                content_type = "application/vnd.apple.mpegurl" if file.suffix == ".m3u8" else "video/mp2t"
                r2.upload_file(str(file), R2_BUCKET, prefix + file.relative_to(out).as_posix(),
                               ExtraArgs={"ContentType": content_type})
        # 全部对象已上传后才发布 ready。
        with SessionLocal() as db:
            asset = db.scalar(select(VideoAsset).where(VideoAsset.id == asset_id).with_for_update())
            if asset.status != "processing" or asset.attempt_count != attempt_number:
                return  # 旧进程不能覆盖已恢复任务的状态。
            asset.master_playlist_key = prefix + "master.m3u8"
            asset.duration_seconds = duration
            asset.status = "ready"
            asset.error_message = None
            asset.updated_at = datetime.now(timezone.utc)
            db.commit()
        log.info("ready asset=%s", asset_id)
    except Exception as error:
        with SessionLocal() as db:
            asset = db.scalar(select(VideoAsset).where(VideoAsset.id == asset_id).with_for_update())
            if asset and asset.status == "processing" and asset.attempt_count == attempt_number:
                asset.status = "failed"
                asset.error_message = str(error)[-2000:]
                asset.updated_at = datetime.now(timezone.utc)
                db.commit()
        log.error("failed asset=%s error_type=%s", asset_id, type(error).__name__)


def recover_stale_tasks():
    """崩溃任务恢复为 failed，不会无限自动重试。单次下载/上传也纳入预留时间。"""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.TRANSCODE_TIMEOUT_SECONDS * 2 + 3600)
    with SessionLocal() as db:
        rows = db.scalars(select(VideoAsset).where(VideoAsset.status == "processing",
                          VideoAsset.processing_started_at < cutoff).with_for_update(skip_locked=True)).all()
        for asset in rows:
            asset.status = "failed"
            asset.error_message = "Processing lease expired; retry after checking worker"
            asset.updated_at = datetime.now(timezone.utc)
        db.commit()


def retry_asset(asset_id):
    with SessionLocal() as db:
        asset = db.get(VideoAsset, UUID(asset_id))
        if not asset or asset.status != "failed":
            raise ValueError("Asset must exist and be failed")
        asset.status = "uploaded"
        asset.error_message = None
        asset.processing_started_at = None
        db.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="只处理一个排队任务")
    parser.add_argument("--retry", help="重试失败的视频资产 UUID")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.retry:
        retry_asset(args.retry)
        return
    while True:
        recover_stale_tasks()
        job = claim_asset()
        if job:
            process_asset(job)
        if args.once:
            return
        if not job:
            time.sleep(5)


if __name__ == "__main__":
    main()
