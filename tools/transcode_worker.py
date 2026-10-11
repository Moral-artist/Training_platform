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

import shutil
import sys

print("Python:", sys.executable)
print("FFmpeg:", shutil.which("ffmpeg"))
print("FFprobe:", shutil.which("ffprobe"))

log = logging.getLogger("transcode")


def run_media_command(args: list[str], timeout: int) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    return result.stdout


def select_levels(height: int, width: int):
    """按短边选择清晰度；仅缩小，不把 720p 伪装成 4K。"""
    source_short = min(height, width)
    requested = sorted(
        set(int(value) for value in settings.HLS_HEIGHTS.split(",") if value.strip())
    )
    if not requested or any(
        h not in {360, 480, 720, 1080, 1440, 2160} for h in requested
    ):
        raise ValueError("Invalid HLS_HEIGHTS")
    levels = [h for h in requested if h <= source_short]
    return levels or [max(2, source_short // 2 * 2)]


def transcode_source(source: Path, output: Path) -> float:
    """CRF 保质压缩 + 峰值码率约束，H264/AAC，4 秒 VOD 分片，多档自适应。"""
    source_format = {".mp4": "mov", ".webm": "matroska"}.get(source.suffix.lower())
    if not source_format:
        raise ValueError("Only MP4 and WebM sources are supported")
    probe = json.loads(
        run_media_command(
            [
                settings.FFPROBE_PATH,
                "-v",
                "error",
                "-f",
                source_format,
                "-protocol_whitelist",
                "file,pipe",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(source),
            ],
            60,
        )
    )
    video = next((v for v in probe["streams"] if v["codec_type"] == "video"), None)
    if not video:
        raise ValueError("No video stream")
    # 禁止附带图片冒充视频，限制不合理尺寸；FFmpeg 应以非特权用户运行。
    if (
        video.get("disposition", {}).get("attached_pic")
        or max(int(video["height"]), int(video["width"])) > 8192
    ):
        raise ValueError("Unsupported source dimensions")
    width, height = int(video["width"]), int(video["height"])
    rotation = next(
        (
            abs(int(v.get("rotation", 0)))
            for v in video.get("side_data_list", [])
            if "rotation" in v
        ),
        0,
    )
    if rotation % 180 == 90:
        width, height = height, width
    levels = select_levels(height, width)
    duration = float(probe["format"].get("duration", 0))
    if duration <= 0 or duration > 12 * 3600:
        raise ValueError("Unsupported source duration")
    master = ["#EXTM3U", "#EXT-X-VERSION:3", "#EXT-X-INDEPENDENT-SEGMENTS"]
    # 峰值约束不等于每秒实际占用；CRF 对静态课件可显著节省空间。
    caps = {360: 1200, 480: 1800, 720: 3500, 1080: 6000, 1440: 10000, 2160: 18000}
    for h in levels:
        folder = output / f"{h}p"
        folder.mkdir(parents=True, exist_ok=True)
        cap = next(value for target, value in caps.items() if h <= target)
        scale = (
            f"scale=-2:{h},setsar=1" if width >= height else f"scale={h}:-2,setsar=1"
        )
        run_media_command(
            [
                settings.FFMPEG_PATH,
                "-nostdin",
                "-y",
                "-v",
                "error",
                "-f",
                source_format,
                "-protocol_whitelist",
                "file,pipe",
                "-i",
                str(source),
                "-map",
                "0:v:0",
                "-map",
                "0:a:0?",
                "-vf",
                scale,
                "-c:v",
                "libx264",
                "-profile:v",
                "high",
                "-preset",
                settings.HLS_PRESET,
                "-pix_fmt",
                "yuv420p",
                "-crf",
                str(settings.HLS_CRF),
                "-maxrate",
                f"{cap}k",
                "-bufsize",
                f"{cap * 2}k",
                "-flags",
                "+cgop",
                "-sc_threshold",
                "0",
                "-force_key_frames",
                "expr:gte(t,n_forced*4)",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-ac",
                "2",
                "-f",
                "hls",
                "-hls_time",
                "4",
                "-hls_playlist_type",
                "vod",
                "-hls_list_size",
                "0",
                "-hls_flags",
                "independent_segments",
                "-hls_segment_filename",
                str(folder / "segment_%05d.ts"),
                str(folder / "index.m3u8"),
            ],
            settings.TRANSCODE_TIMEOUT_SECONDS,
        )
        # 从实际编码结果读取宽高/codec，清晰度选择器才有正确的 1080/2K/4K 标签。
        encoded = json.loads(
            run_media_command(
                [
                    settings.FFPROBE_PATH,
                    "-v",
                    "error",
                    "-show_streams",
                    "-of",
                    "json",
                    str(folder / "index.m3u8"),
                ],
                60,
            )
        )
        stream = next(v for v in encoded["streams"] if v["codec_type"] == "video")
        # 以实际 H264 SPS profile/level 构建 codec 字段，避免浏览器误判支持能力。
        # RFC 6381 profile 100 / constraints 0；level 由 ffprobe 给出。
        codecs = f"avc1.6400{int(stream.get('level', 40)):02x}"
        if any(v["codec_type"] == "audio" for v in encoded["streams"]):
            codecs += ",mp4a.40.2"
        master += [
            f'#EXT-X-STREAM-INF:BANDWIDTH={(cap + 128) * 1000},RESOLUTION={stream["width"]}x{stream["height"]},CODECS="{codecs}"',
            f"{h}p/index.m3u8",
        ]
    (output / "master.m3u8").write_text("\n".join(master) + "\n")
    return duration


def claim_asset():
    """行锁避免两个转码进程领取同一任务；不持有长事务。"""
    with SessionLocal() as db:
        asset = db.scalar(
            select(VideoAsset)
            .where(VideoAsset.status == "uploaded")
            .order_by(VideoAsset.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
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
            if not 0 < metadata["ContentLength"] <= settings.MAX_UPLOAD_BYTES:
                raise ValueError("Source size exceeds allowed size")
            r2.download_file(R2_BUCKET, source_key, str(source))
            if not 0 < source.stat().st_size <= settings.MAX_UPLOAD_BYTES:
                raise ValueError("Downloaded source size invalid")
            # 对真正下载的内容再次核对 SHA256；不能信任浏览器的重复文件标记。
            import hashlib

            digest = hashlib.sha256()
            with source.open("rb") as handle:
                for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
                    digest.update(chunk)
            actual_hash = digest.hexdigest()
            with SessionLocal() as db:
                record = db.get(VideoAsset, asset_id)
                if record.content_hash and record.content_hash != actual_hash:
                    raise ValueError(
                        "Source hash mismatch; discard and upload the correct file"
                    )
                record.verified_hash = actual_hash
                db.commit()
            out = root / "hls"
            out.mkdir()
            duration = transcode_source(source, out)
            files = sorted(out.rglob("*"), key=lambda p: p.name == "master.m3u8")
            for file in files:
                if not file.is_file():
                    continue
                content_type = (
                    "application/vnd.apple.mpegurl"
                    if file.suffix == ".m3u8"
                    else "video/mp2t"
                )
                r2.upload_file(
                    str(file),
                    R2_BUCKET,
                    prefix + file.relative_to(out).as_posix(),
                    ExtraArgs={"ContentType": content_type},
                )
        # 全部对象已上传后才发布 ready。
        with SessionLocal() as db:
            asset = db.scalar(
                select(VideoAsset).where(VideoAsset.id == asset_id).with_for_update()
            )
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
            asset = db.scalar(
                select(VideoAsset).where(VideoAsset.id == asset_id).with_for_update()
            )
            if (
                asset
                and asset.status == "processing"
                and asset.attempt_count == attempt_number
            ):
                asset.status = "failed"
                asset.error_message = str(error)[-2000:]
                asset.updated_at = datetime.now(timezone.utc)
                db.commit()
        log.error("failed asset=%s error_type=%s", asset_id, type(error).__name__)


def recover_stale_tasks():
    """崩溃任务恢复为 failed，不会无限自动重试。单次下载/上传也纳入预留时间。"""
    # 每档转码分别有 timeout；租约须覆盖所有档位，防止 4K 长视频被误判崩溃。
    level_count = len(settings.HLS_HEIGHTS.split(","))
    cutoff = datetime.now(timezone.utc) - timedelta(
        seconds=settings.TRANSCODE_TIMEOUT_SECONDS * level_count + 7200
    )
    with SessionLocal() as db:
        rows = db.scalars(
            select(VideoAsset)
            .where(
                VideoAsset.status == "processing",
                VideoAsset.processing_started_at < cutoff,
            )
            .with_for_update(skip_locked=True)
        ).all()
        for asset in rows:
            asset.status = "failed"
            asset.error_message = (
                "Processing lease expired; retry after checking worker"
            )
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
