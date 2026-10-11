-- 在 001 之后执行；事务由 tools.db_setup 管理。可重复运行。
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS deleted_at timestamptz;
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS revision integer NOT NULL DEFAULT 1;
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS request_id uuid;
CREATE UNIQUE INDEX IF NOT EXISTS uq_lessons_request_id ON lessons(request_id);
ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS content_hash varchar(64);
ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS verified_hash varchar(64);
ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS multipart_upload_id text;
CREATE UNIQUE INDEX IF NOT EXISTS uq_video_owner_hash ON video_assets(created_by, content_hash);
ALTER TABLE IF EXISTS exam_attempts ALTER COLUMN score SET DEFAULT 0;
ALTER TABLE IF EXISTS exam_attempts ALTER COLUMN passed SET DEFAULT false;
ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS upload_part_size integer;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS auth_version integer NOT NULL DEFAULT 0;
ALTER TABLE IF EXISTS exams ADD COLUMN IF NOT EXISTS deleted_at timestamptz;
