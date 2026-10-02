from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select
from data_model.data_model import LessonAccess, Account, VideoAsset, CustomedPlan, PlanLesson
from dependencies.auth import get_current_session
from main import app
from conftest import ADMIN, STUDENT, ADMIN_USER, STUDENT_USER, ASSET, PREFIX

CSRF = {'X-CSRF-Token': 'test-csrf'}

def authorize(db):
    db.add(LessonAccess(account_id=STUDENT, lesson_id=1, granted_by=ADMIN)); db.commit()

def test_missing_login(context):
    client, _, _ = context
    async def missing(): raise HTTPException(401, 'Not authenticated')
    app.dependency_overrides[get_current_session] = missing
    assert client.get('/api/lessons/majors/1/lessonlist').status_code == 401
    assert client.post('/api/lessons/1/play', headers=CSRF).status_code == 401


def test_list_is_filtered_and_no_video_keys(context):
    client, db, identity = context
    result = client.get('/api/lessons/majors/1/lessonlist')
    assert result.status_code == 200 and result.json()['total_lessons'] == 0
    authorize(db)
    data = client.get('/api/lessons/majors/1/lessonlist').json()
    assert data['total_lessons'] == 1 and data['total_pages'] == 1
    assert data['lessonlist'][0]['video_status'] == 'ready'
    assert 'video_url' not in data['lessonlist'][0]
    assert 'videos/' not in str(data)
    assert client.get('/api/lessons/majors/1/lessonlist?page_size=0').status_code == 422
    assert client.get('/api/lessons/majors/1/lessonlist?current_page=0').status_code == 422


def test_detail_and_play_deny_ungranted_student(context):
    client, db, _ = context
    assert client.get('/api/lessons/1/detail').status_code == 403
    assert client.post('/api/lessons/1/play', headers=CSRF).status_code == 403
    assert client.get('/api/lessons/999/detail').status_code == 404


def test_own_learning_plan_does_not_grant_playback(context):
    client, db, _ = context
    plan = CustomedPlan(id=1, user_id=STUDENT_USER, plan_name='mine', source_type='manual', status='not_started')
    db.add(plan); db.flush()
    db.add(PlanLesson(plan_id=1, lesson_id=1, lesson_order=1, completed=False)); db.commit()
    assert client.post('/api/lessons/1/play', headers=CSRF).status_code == 403


def test_playback_requires_csrf_and_signs_short_scoped_token(context):
    import jwt
    client, db, _ = context
    authorize(db)
    assert client.post('/api/lessons/1/play').status_code == 403
    response = client.post('/api/lessons/1/play', headers=CSRF)
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    data = response.json()
    claims = jwt.decode(data['token'], 'test-only-secret-32-bytes-0123456789', algorithms=['HS256'], audience='training-video', issuer='training-api')
    assert claims['asset'] == str(ASSET) and claims['prefix'] == PREFIX
    assert claims['exp'] - claims['iat'] == 300
    assert data['refresh_after'] == 240


def test_unready_and_disabled_account_denied(context):
    client, db, _ = context
    authorize(db)
    asset = db.get(VideoAsset, ASSET); asset.status = 'processing'; db.commit()
    assert client.post('/api/lessons/1/play', headers=CSRF).status_code == 409
    account = db.get(Account, STUDENT); account.is_active = False; db.commit()
    assert client.get('/api/lessons/1/detail').status_code == 403


def test_admin_grant_revoke_are_idempotent_and_affect_new_tokens(context):
    client, db, identity = context
    assert client.put(f'/api/lessons/1/access/{STUDENT}', headers=CSRF).status_code == 403
    identity['user_id'] = str(ADMIN_USER)
    for _ in range(2): assert client.put(f'/api/lessons/1/access/{STUDENT}', headers=CSRF).status_code == 200
    identity['user_id'] = str(STUDENT_USER)
    assert client.post('/api/lessons/1/play', headers=CSRF).status_code == 200
    identity['user_id'] = str(ADMIN_USER)
    assert client.delete(f'/api/lessons/1/access/{STUDENT}', headers=CSRF).status_code == 200
    identity['user_id'] = str(STUDENT_USER)
    assert client.post('/api/lessons/1/play', headers=CSRF).status_code == 403


def test_upload_contract_size_complete_and_idempotency(context, monkeypatch):
    client, db, identity = context
    body = {'filename': 'lesson.mp4', 'content_type': 'video/mp4', 'size': 100}
    assert client.post('/api/lessons_video/upload_token', json=body, headers=CSRF).status_code == 403
    identity['user_id'] = str(ADMIN_USER)
    monkeypatch.setattr('Router.lessons.lesson_video.r2.generate_presigned_url', lambda **kwargs: 'https://r2.example.com/upload')
    result = client.post('/api/lessons_video/upload_token', json=body, headers=CSRF)
    assert result.status_code == 200
    asset_id = result.json()['asset_id']
    assert 'object_key' not in result.json()
    monkeypatch.setattr('Router.lessons.lesson_video.r2.head_object', lambda **kwargs: {'ContentLength': 99, 'ContentType': 'video/mp4'})
    assert client.post(f'/api/lessons_video/{asset_id}/complete', headers=CSRF).status_code == 400
    monkeypatch.setattr('Router.lessons.lesson_video.r2.head_object', lambda **kwargs: {'ContentLength': 100, 'ContentType': 'video/mp4'})
    for _ in range(2): assert client.post(f'/api/lessons_video/{asset_id}/complete', headers=CSRF).json()['status'] == 'uploaded'
    assert client.get(f'/api/lessons_video/{asset_id}/status').status_code == 200
    assert client.post('/api/lessons_video/upload_token', json={**body, 'size': 300*1024*1024+1}, headers=CSRF).status_code == 422
    assert client.post('/api/lessons_video/upload_token', json={**body, 'filename': 'a.exe'}, headers=CSRF).status_code == 400


def test_course_create_asset_and_pending_rejected(context):
    client, db, identity = context
    identity['user_id'] = str(ADMIN_USER)
    body = {'system_id': 1, 'lesson_name': 'Lesson B', 'description': 'text', 'video_asset_id': str(ASSET)}
    asset = db.get(VideoAsset, ASSET); asset.status = 'pending_upload'; db.commit()
    assert client.post('/api/lessons/lessonsubmit', json=body, headers=CSRF).status_code == 409
    asset.status = 'uploaded'; db.commit()
    response = client.post('/api/lessons/lessonsubmit', json=body, headers=CSRF)
    assert response.status_code == 200 and response.json()['lesson_id'] == 2
    assert client.post('/api/lessons/lessonsubmit', json=body, headers=CSRF).status_code == 400


def test_retry_only_failed_assets_and_no_source_paths(context):
    client, db, identity = context
    identity['user_id'] = str(ADMIN_USER)
    assert client.post(f'/api/lessons_video/{ASSET}/retry', headers=CSRF).status_code == 409
    asset = db.get(VideoAsset, ASSET); asset.status = 'failed'; asset.error_message = 'internal secret path'; db.commit()
    response = client.get(f'/api/lessons_video/{ASSET}/status')
    assert 'internal secret path' not in response.text
    assert client.post(f'/api/lessons_video/{ASSET}/retry', headers=CSRF).json()['status'] == 'uploaded'


def test_account_search_is_admin_only_and_excludes_credentials(context):
    client, _, identity = context
    assert client.get('/api/lessons/access_accounts').status_code == 403
    identity['user_id'] = str(ADMIN_USER)
    response = client.get('/api/lessons/access_accounts?search=student')
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['account_id'] == str(STUDENT)
    assert 'password' not in response.text and 'csrf_token' not in response.text
