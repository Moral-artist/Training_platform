from sqlalchemy import Integer, String, DateTime, ForeignKey, UUID, text
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
