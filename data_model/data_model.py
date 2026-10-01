from symtable import Class

from sqlalchemy import (Integer, String, DateTime,
                        ForeignKey, UUID, text, CheckConstraint,
                        UniqueConstraint, Boolean, func)

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
    token: Mapped[str] = mapped_column(
        String,
    )
    expired: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
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
    lesson_video_url: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    update_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("accounts.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=False,
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

