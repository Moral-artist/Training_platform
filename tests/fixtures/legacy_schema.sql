-- Legacy schema based on supplied (6), with the optional poster column omitted to match the user's actual table.

CREATE TABLE permissions (
	id VARCHAR NOT NULL, 
	permission_name VARCHAR NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE TABLE roles (
	id VARCHAR NOT NULL, 
	role_name VARCHAR NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE TABLE users (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	user_name VARCHAR NOT NULL, 
	character VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT character_check CHECK (character IN ('engineer', 'operator', 'shiftleader'))
)

;

CREATE TABLE accounts (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	password VARCHAR NOT NULL, 
	email VARCHAR NOT NULL, 
	token VARCHAR NOT NULL, 
	expired TIMESTAMP WITH TIME ZONE, 
	user_id UUID NOT NULL, 
	role_id VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE ON UPDATE CASCADE
)

;

CREATE TABLE role_permission (
	role_id VARCHAR NOT NULL, 
	permission_id VARCHAR NOT NULL, 
	PRIMARY KEY (role_id, permission_id), 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(permission_id) REFERENCES permissions (id) ON DELETE CASCADE ON UPDATE CASCADE
)

;

CREATE TABLE lessons (
	id SERIAL NOT NULL, 
	description VARCHAR NOT NULL, 
	lesson_name VARCHAR NOT NULL, 
	lesson_video_url VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	update_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	created_by UUID NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (lesson_name), 
	FOREIGN KEY(created_by) REFERENCES accounts (id) ON DELETE SET NULL ON UPDATE CASCADE
)

;

CREATE TABLE systems (
	id SERIAL NOT NULL, 
	system_name VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	create_by UUID NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (system_name), 
	FOREIGN KEY(create_by) REFERENCES accounts (id) ON DELETE CASCADE ON UPDATE CASCADE
)

;

CREATE TABLE training_plan (
	id SERIAL NOT NULL, 
	plan_name VARCHAR NOT NULL, 
	description VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	created_by UUID NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by) REFERENCES accounts (id) ON DELETE SET NULL ON UPDATE CASCADE
)

;

CREATE TABLE video_assets (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
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
)

;

CREATE TABLE customed_plan (
	id SERIAL NOT NULL, 
	user_id UUID NOT NULL, 
	template_plan_id INTEGER, 
	plan_name VARCHAR NOT NULL, 
	source_type VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	CHECK (source_type IN ('preset', 'personalized', 'manual')), 
	CHECK (status IN ('not_started', 'in_progress', 'completed', 'paused')), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(template_plan_id) REFERENCES training_plan (id) ON DELETE SET NULL ON UPDATE CASCADE
)

;

CREATE TABLE lesson_access (
	account_id UUID NOT NULL, 
	lesson_id INTEGER NOT NULL, 
	granted_by UUID, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (account_id, lesson_id), 
	FOREIGN KEY(account_id) REFERENCES accounts (id) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(lesson_id) REFERENCES lessons (id) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(granted_by) REFERENCES accounts (id) ON DELETE SET NULL ON UPDATE CASCADE
)

;

CREATE TABLE system_lesson (
	system_id INTEGER NOT NULL, 
	lesson_id INTEGER NOT NULL, 
	PRIMARY KEY (system_id, lesson_id), 
	FOREIGN KEY(system_id) REFERENCES systems (id) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(lesson_id) REFERENCES lessons (id) ON DELETE CASCADE ON UPDATE CASCADE
)

;

CREATE TABLE training_plan_lesson (
	plan_id INTEGER NOT NULL, 
	lesson_id INTEGER NOT NULL, 
	lesson_order INTEGER NOT NULL, 
	PRIMARY KEY (plan_id, lesson_id), 
	CONSTRAINT unique_order UNIQUE (plan_id, lesson_order), 
	FOREIGN KEY(plan_id) REFERENCES training_plan (id) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(lesson_id) REFERENCES lessons (id) ON DELETE CASCADE ON UPDATE CASCADE
)

;

CREATE TABLE plan_lesson (
	lesson_id INTEGER NOT NULL, 
	plan_id INTEGER NOT NULL, 
	completed BOOLEAN NOT NULL, 
	start_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	lesson_order INTEGER NOT NULL, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (lesson_id, plan_id), 
	CONSTRAINT unique_plan_order UNIQUE (plan_id, lesson_order), 
	FOREIGN KEY(lesson_id) REFERENCES lessons (id) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(plan_id) REFERENCES customed_plan (id) ON DELETE CASCADE ON UPDATE CASCADE
)

;
