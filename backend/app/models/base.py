from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import TypeVar

from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

BIGINT_SQL = BigInteger().with_variant(Integer, "sqlite")

_StrEnumT = TypeVar("_StrEnumT", bound=StrEnum)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def enum_values(enum_cls: type[_StrEnumT]) -> tuple[str, ...]:
    return tuple(member.value for member in enum_cls)


def enum_check_clause(enum_cls: type[_StrEnumT], *, column_name: str) -> str:
    values_sql = ", ".join(repr(value) for value in enum_values(enum_cls))
    return f"{column_name} IN ({values_sql})"


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class SoftArchiveMixin:
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None

    def archive(self, *, archived_at: datetime | None = None) -> None:
        self.archived_at = archived_at or utcnow()

    def restore(self) -> None:
        self.archived_at = None


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    ATTENTION = "attention"
    RECOVERING = "recovering"
    CRITICAL = "critical"


class PlantEventType(StrEnum):
    WATERING = "watering"
    FERTILIZATION = "fertilization"
    REPOTTING = "repotting"
    PRUNING = "pruning"
    LOCATION_CHANGE = "location_change"
    BLOOM = "bloom"
    NEW_GROWTH = "new_growth"
    WILT = "wilt"
    YELLOW_LEAVES = "yellow_leaves"
    PEST = "pest"
    OBSERVATION = "observation"
    PHOTO_ADDED = "photo_added"


class PhotoType(StrEnum):
    ROUTINE = "routine"
    PROBLEM = "problem"
    PROGRESS = "progress"


class MaintenanceTaskStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"
    CANCELED = "canceled"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    READ = "read"
    DISCARDED = "discarded"
    FAILED = "failed"


class AIMessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
