"""真实 FFmpeg 验收：源清晰度保留、生成多档 HLS、分片可解码。"""

import json
import shutil
import subprocess
import pytest
from tools import transcode_worker as worker
from data_model.config import settings


@pytest.mark.parametrize(
    "width,height,seconds,expected",
    [(1920, 1080, 1, [720, 1080]), (3840, 2160, 0.6, [720, 1080, 1440, 2160])],
)
def test_real_high_resolution_hls(
    tmp_path, monkeypatch, width, height, seconds, expected
):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg is required")
    monkeypatch.setattr(settings, "FFMPEG_PATH", shutil.which("ffmpeg"))
    monkeypatch.setattr(settings, "FFPROBE_PATH", shutil.which("ffprobe"))
    monkeypatch.setattr(settings, "HLS_HEIGHTS", "720,1080,1440,2160")
    source = tmp_path / "source.mp4"
    out = tmp_path / "hls"
    out.mkdir()
    subprocess.run(
        [
            settings.FFMPEG_PATH,
            "-nostdin",
            "-y",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size={width}x{height}:rate=5",
            "-t",
            str(seconds),
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
        timeout=90,
    )
    assert worker.transcode_source(source, out) > 0
    manifest = (out / "master.m3u8").read_text()
    for h in expected:
        assert f"{h}p/index.m3u8" in manifest
        probe = json.loads(
            subprocess.check_output(
                [
                    settings.FFPROBE_PATH,
                    "-v",
                    "error",
                    "-show_streams",
                    "-of",
                    "json",
                    str(out / f"{h}p/index.m3u8"),
                ],
                timeout=30,
            )
        )
        video = next(s for s in probe["streams"] if s["codec_type"] == "video")
        assert video["height"] == h and video["width"] == h * 16 // 9
        assert video["codec_name"] == "h264"
    assert (
        "2160p/index.m3u8" in manifest
        if height == 2160
        else "2160p/index.m3u8" not in manifest
    )
