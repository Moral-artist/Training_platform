from symtable import Class

from sqlalchemy import (Integer, String, DateTime,
                        ForeignKey, UUID, text, CheckConstraint,
                        UniqueConstraint, Boolean, func, Text, BigInteger, Float)

from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from data_model.core_database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    user_name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    character: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    __table_args__ = (
        CheckConstraint("character IN ('engineer', 'operator', 'shiftleader')",
                        name="character_check"),
    )

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    password: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    token: Mapped[str | None] = mapped_column(
        String,
    )
    expired: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        unique=True,
    )
    role_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("roles.id", onupdate="CASCADE", ondelete="CASCADE")
    )

class Roles(Base):
    __tablename__ = "roles"
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )
    role_name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

class Permissions(Base):
    __tablename__ = "permissions"
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )
    permission_name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

class RolePermission(Base):
    __tablename__ = "role_permission"
    role_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("roles.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    )
    permission_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("permissions.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    )

class Systems(Base):
    __tablename__ = "systems"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    system_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True
    )

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    create_by: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("accounts.id", onupdate="CASCADE", ondelete="CASCADE"),
    )

class LessonAccess(Base):
    __tablename__ = "lesson_access"

    # 修改1001
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("accounts.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    lesson_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lessons.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID,
        ForeignKey("accounts.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

class Lessons(Base):
    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    description: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    lesson_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True
    )
    # 旧数据迁移期间保留，新的课程不再写播放 URL。
    lesson_video_url: Mapped[str | None] = mapped_column(String, nullable=True)
    video_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("video_assets.id", ondelete="RESTRICT"), index=True
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    update_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID,
        ForeignKey("accounts.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )


class VideoAsset(Base):
    __tablename__ = "video_assets"

    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'pending_upload', 'uploaded', 'processing', "
            "'ready', 'failed', 'migration_pending'"
            ")",
            name="ck_video_assets_status",
        ),
        CheckConstraint(
            "status <> 'ready' OR master_playlist_key IS NOT NULL",
            name="ck_video_assets_ready_manifest",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    declared_size: Mapped[int | None] = mapped_column(BigInteger)
    content_type: Mapped[str | None] = mapped_column(String(64))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    # 原始视频在 R2 中的路径
    source_object_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    # 转码完成后的 master.m3u8 路径
    master_playlist_key: Mapped[str | None] = mapped_column(Text)

    # 可选：封面图片在 R2 中的路径
    poster_object_key: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'pending_upload'"),
    )

    error_message: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID,
        ForeignKey(
            "accounts.id",
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now(),
    )



class SystemLesson(Base):
    __tablename__ = "system_lesson"
    system_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("systems.id",onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    )
    lesson_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lessons.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    )

class TrainingPlan(Base):
    __tablename__ = "training_plan"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    plan_name: Mapped[str] = mapped_column(
        String,
    )
    description: Mapped[str] = mapped_column(
        String
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("accounts.id", onupdate="CASCADE", ondelete="SET NULL"),
    )

class TrainingPlanLesson(Base):
    __tablename__ = "training_plan_lesson"

    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("training_plan.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    )
    lesson_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lessons.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    )

    lesson_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "lesson_order",
            name='unique_order'
        ),
    )

class CustomedPlan(Base):
    __tablename__ = "customed_plan"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
    )
    template_plan_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "training_plan.id",
            onupdate="CASCADE",
            ondelete="SET NULL"
        ),
        nullable=True
    )
    plan_name: Mapped[str] = mapped_column(
        String,
    )
    source_type: Mapped[str] = mapped_column(
        String
    )
    status: Mapped[str] = mapped_column(
        String,
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    __table_args__ = (
        CheckConstraint("source_type IN ('preset', 'personalized', 'manual')" ),
        CheckConstraint("status IN ('not_started', 'in_progress', 'completed', 'paused')" ),
    )

class PlanLesson(Base):
    __tablename__ = "plan_lesson"
    lesson_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lessons.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    )
    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customed_plan.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    )
    completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    lesson_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "lesson_order",
            name='unique_plan_order'
        ),
    )

