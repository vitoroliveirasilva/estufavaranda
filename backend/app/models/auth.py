from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BIGINT_SQL, Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    devices = relationship(
        "Device",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    plants = relationship("Plant", back_populates="user", passive_deletes=True)
    notifications = relationship(
        "NotificationEvent", back_populates="user", passive_deletes=True
    )
    ai_conversations = relationship(
        "AIConversation", back_populates="user", passive_deletes=True
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
        Index("ix_refresh_tokens_revoked_at", "revoked_at"),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_SQL, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    device_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    user = relationship("User", back_populates="refresh_tokens")


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    __table_args__ = (
        Index("ix_login_attempts_email", "email"),
        Index("ix_login_attempts_ip", "ip"),
        Index("ix_login_attempts_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class AuthRateLimitEvent(Base):
    __tablename__ = "auth_rate_limit_events"
    __table_args__ = (
        Index("ix_auth_rate_limit_events_action", "action"),
        Index("ix_auth_rate_limit_events_scope_key", "scope_key"),
        Index("ix_auth_rate_limit_events_created_at", "created_at"),
        Index(
            "ix_auth_rate_limit_events_action_scope_created_at",
            "action",
            "scope_key",
            "created_at",
        ),
        CheckConstraint("action <> ''", name="ck_auth_rate_limit_events_action_not_blank"),
        CheckConstraint(
            "scope_key <> ''",
            name="ck_auth_rate_limit_events_scope_key_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("ix_password_reset_tokens_user_id", "user_id"),
        Index("ix_password_reset_tokens_expires_at", "expires_at"),
        Index("ix_password_reset_tokens_used_at", "used_at"),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_SQL, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    user = relationship("User", back_populates="password_reset_tokens")


class Device(Base, TimestampMixin):
    __tablename__ = "devices"
    __table_args__ = (
        Index("ix_devices_user_id", "user_id"),
        CheckConstraint(
            "platform <> ''",
            name="ck_devices_platform_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_SQL,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    push_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user = relationship("User", back_populates="devices")
