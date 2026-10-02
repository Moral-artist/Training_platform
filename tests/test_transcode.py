from pathlib import Path
from sqlalchemy.orm import Session
from data_model.data_model import VideoAsset
from tools import transcode_worker as worker
from conftest import ASSET


def configure_job(context, monkeypatch, fail_upload=False):
    _, db, _ = context
    asset = db.get(VideoAsset, ASSET)
    asset.status = 'uploaded'; db.commit()
    monkeypatch.setattr(worker, 'SessionLocal', lambda: Session(db.bind, expire_on_commit=False))
    monkeypatch.setattr(worker.r2, 'head_object', lambda **kwargs: {'ContentLength': 100})
    def download(bucket, key, filename):
        Path(filename).write_bytes(b'x' * 100)
    monkeypatch.setattr(worker.r2, 'download_file', download)
    def encode(source, output):
        (output / '360p').mkdir()
        (output / '360p/segment_00000.ts').write_bytes(b'ts')
        (output / '360p/index.m3u8').write_text('#EXTM3U\nsegment_00000.ts\n')
        (output / 'master.m3u8').write_text('#EXTM3U\n360p/index.m3u8\n')
        return 12.5
    monkeypatch.setattr(worker, 'transcode_source', encode)
    uploads = []
    def upload(filename, bucket, key, **kwargs):
        if fail_upload:
            raise RuntimeError('simulated upload failure')
        uploads.append(key)
        with Session(db.bind) as check:
            assert check.get(VideoAsset, ASSET).status == 'processing'
    monkeypatch.setattr(worker.r2, 'upload_file', upload)
    return db, uploads


def test_queue_publish_only_after_all_files_uploaded(context, monkeypatch):
    db, uploads = configure_job(context, monkeypatch)
    job = worker.claim_asset()
    assert worker.claim_asset() is None
    worker.process_asset(job)
    db.expire_all(); asset = db.get(VideoAsset, ASSET)
    assert asset.status == 'ready' and asset.duration_seconds == 12.5
    assert len(uploads) == 3 and uploads[-1].endswith('/master.m3u8')
    assert asset.master_playlist_key == uploads[-1]
    assert asset.attempt_count == 1


def test_failure_retry_returns_to_queue(context, monkeypatch):
    db, _ = configure_job(context, monkeypatch, fail_upload=True)
    worker.process_asset(worker.claim_asset())
    db.expire_all(); asset = db.get(VideoAsset, ASSET)
    assert asset.status == 'failed'
    assert 'simulated upload failure' in asset.error_message
    worker.retry_asset(str(ASSET))
    db.expire_all(); assert db.get(VideoAsset, ASSET).status == 'uploaded'


def test_stale_job_does_not_publish_over_new_attempt(context, monkeypatch):
    db, _ = configure_job(context, monkeypatch)
    job = worker.claim_asset()
    db.expire_all(); asset = db.get(VideoAsset, ASSET)
    asset.attempt_count += 1
    db.commit()
    worker.process_asset(job)
    db.expire_all(); assert db.get(VideoAsset, ASSET).status == 'processing'
