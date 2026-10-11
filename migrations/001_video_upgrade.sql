-- Upgrade the supplied (6) backend schema. Run inside one transaction.
-- Recommended: python -m tools.db_setup migrate --apply
-- Existing video URLs are retained and are NOT treated as R2 object keys.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
DO $$ BEGIN
    IF EXISTS (SELECT user_id FROM accounts GROUP BY user_id HAVING count(*) > 1) THEN
        RAISE EXCEPTION 'Duplicate accounts.user_id: resolve the mapping before migrating';
    END IF;
END $$;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;
ALTER TABLE accounts ALTER COLUMN token DROP NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_accounts_user_id ON accounts(user_id);
CREATE TABLE IF NOT EXISTS video_assets (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	declared_size BIGINT, 
	content_type VARCHAR(64), 
	duration_seconds FLOAT, 
	processing_started_at TIMESTAMP WITH TIME ZONE, 
	attempt_count INTEGER DEFAULT 0 NOT NULL, 
	source_object_key TEXT NOT NULL, 
	master_playlist_key TEXT, 
	status VARCHAR(32) DEFAULT 'pending_upload' NOT NULL, 
	error_message TEXT, 
	created_by UUID, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_video_assets_status CHECK (status IN ('pending_upload', 'uploaded', 'processing', 'ready', 'failed', 'migration_pending')), 
	CONSTRAINT ck_video_assets_ready_manifest CHECK (status <> 'ready' OR master_playlist_key IS NOT NULL), 
	UNIQUE (source_object_key), 
	FOREIGN KEY(created_by) REFERENCES accounts (id) ON DELETE SET NULL ON UPDATE CASCADE
);

ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS declared_size bigint;
ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS content_type varchar(64);
ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS duration_seconds double precision;
ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS processing_started_at timestamptz;
ALTER TABLE video_assets ADD COLUMN IF NOT EXISTS attempt_count integer NOT NULL DEFAULT 0;
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS video_asset_id uuid;
ALTER TABLE lessons ALTER COLUMN lesson_video_url DROP NOT NULL;
ALTER TABLE lessons ALTER COLUMN created_by DROP NOT NULL;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'lessons'::regclass AND contype = 'f'
        AND confrelid = 'video_assets'::regclass
        AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'lessons'::regclass AND attname = 'video_asset_id')]::smallint[]
    ) THEN
        ALTER TABLE lessons ADD CONSTRAINT fk_lessons_video_asset FOREIGN KEY (video_asset_id) REFERENCES video_assets(id) ON DELETE RESTRICT;
    END IF;
END $$;
CREATE TABLE IF NOT EXISTS lesson_access (
	account_id UUID NOT NULL, 
	lesson_id INTEGER NOT NULL, 
	granted_by UUID, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (account_id, lesson_id), 
	FOREIGN KEY(account_id) REFERENCES accounts (id) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(lesson_id) REFERENCES lessons (id) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(granted_by) REFERENCES accounts (id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_lessons_video_asset_id ON lessons(video_asset_id);
CREATE INDEX IF NOT EXISTS ix_video_assets_queue ON video_assets(status, created_at);
CREATE INDEX IF NOT EXISTS ix_lesson_access_lesson_id ON lesson_access(lesson_id);
