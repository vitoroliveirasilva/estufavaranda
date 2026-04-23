from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BIGINT_SQL, Base, TimestampMixin


class NotificationEvent(Base):
    __tablename__ = "notification_events"
    __table_args__ = (
        Index("ix_notification_events_user_id", "user_id"),
        Index("ix_notification_events_plant_id", "plant_id"),
        Index("ix_notification_events_status", "status"),
        Index("ix_notification_events_dedupe_key", "dedupe_key", unique=True),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_SQL, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[int | None] = mapped_column(
        BIGINT_SQL, ForeignKey("plants.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    dedupe_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    discarded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user = relationship("User", back_populates="notifications")
    plant = relationship("Plant", back_populates="notifications")
    dispatches = relationship(
        "NotificationDispatch",
        back_populates="notification_event",
        cascade="all, delete-orphan",
    )


class NotificationDispatch(Base, TimestampMixin):
    __tablename__ = "notification_dispatches"

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    notification_event_id: Mapped[int] = mapped_column(
        BIGINT_SQL,
        ForeignKey("notification_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    dispatched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    provider_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    notification_event = relationship("NotificationEvent", back_populates="dispatches")
