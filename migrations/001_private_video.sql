-- PostgreSQL；先备份，在测试库执行。不要用 create_all 代替迁移。
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- 可以停用账号
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;
-- 原 token 已不用于 Redis 登录；新注册没有为它赋值。

DO $$ BEGIN
    IF EXISTS (SELECT user_id FROM accounts GROUP BY user_id HAVING count(*) > 1) THEN
        RAISE EXCEPTION 'Duplicate accounts.user_id; review and resolve duplicates before migration';
    END IF;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS uq_accounts_user_id ON accounts(user_id);

ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS declared_size bigint;
ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS content_type varchar(64);
ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS duration_seconds double precision;
ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS processing_started_at timestamptz;
ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS attempt_count integer NOT NULL DEFAULT 0;
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS video_asset_id uuid;
ALTER TABLE lessons ALTER COLUMN lesson_video_url DROP NOT NULL;
ALTER TABLE lessons ALTER COLUMN created_by DROP NOT NULL;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'lessons'::regclass AND conname = 'fk_lessons_video_asset') THEN
        ALTER TABLE lessons ADD CONSTRAINT fk_lessons_video_asset FOREIGN KEY (video_asset_id) REFERENCES video_assets(id) ON DELETE RESTRICT;
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS ix_lessons_video_asset_id ON lessons(video_asset_id);
CREATE INDEX IF NOT EXISTS ix_video_assets_queue ON video_assets(status, created_at);
CREATE INDEX IF NOT EXISTS ix_lesson_access_lesson_id ON lesson_access(lesson_id);
COMMIT;
-- 保留 lesson_video_url 里的原值用于手工迁移，不自动猜测 URL 对应的 R2 key。
-- 已存在的 video_assets/lesson_access 若结构与模型不同，先核对再执行。
