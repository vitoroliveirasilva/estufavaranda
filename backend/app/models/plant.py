from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    AIMessageRole,
    BIGINT_SQL,
    Base,
    HealthStatus,
    MaintenanceTaskStatus,
    PhotoType,
    PlantEventType,
    SoftArchiveMixin,
    TimestampMixin,
    enum_check_clause,
)


class Plant(Base, TimestampMixin, SoftArchiveMixin):
    __tablename__ = "plants"
    __table_args__ = (
        Index("ix_plants_user_id", "user_id"),
        Index("ix_plants_health_status", "health_status"),
        CheckConstraint(
            enum_check_clause(HealthStatus, column_name="health_status"),
            name="ck_plants_health_status",
        ),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_SQL, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(150), nullable=True)
    acquisition_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    environment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    light_exposure: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ventilation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vase_description: Mapped[str | None] = mapped_column(String(150), nullable=True)
    substrate_description: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )
    location_label: Mapped[str | None] = mapped_column(String(150), nullable=True)
    city_name: Mapped[str | None] = mapped_column(
        String(150), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    health_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=HealthStatus.ATTENTION.value,
        server_default=text(f"'{HealthStatus.ATTENTION.value}'"),
    )

    user = relationship("User", back_populates="plants")
    events = relationship(
        "PlantEvent",
        back_populates="plant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    photos = relationship(
        "PlantPhoto",
        back_populates="plant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    watering_logs = relationship(
        "WateringLog",
        back_populates="plant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    fertilization_logs = relationship(
        "FertilizationLog",
        back_populates="plant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    maintenance_tasks = relationship(
        "MaintenanceTask",
        back_populates="plant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    climate_snapshots = relationship(
        "ClimateSnapshot",
        back_populates="plant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notifications = relationship(
        "NotificationEvent",
        back_populates="plant",
        passive_deletes=True,
    )
    diagnoses = relationship(
        "PlantDiagnosis",
        back_populates="plant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    ai_conversations = relationship(
        "AIConversation",
        back_populates="plant",
        passive_deletes=True,
    )


class PlantEvent(Base, TimestampMixin):
    __tablename__ = "plant_events"
    __table_args__ = (
        Index("ix_plant_events_plant_id", "plant_id"),
        Index("ix_plant_events_event_type", "event_type"),
        Index("ix_plant_events_occurred_at", "occurred_at"),
        CheckConstraint(
            enum_check_clause(PlantEventType, column_name="event_type"),
            name="ck_plant_events_event_type",
        ),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(
        BIGINT_SQL, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    plant = relationship("Plant", back_populates="events")


class PlantPhoto(Base, TimestampMixin):
    __tablename__ = "plant_photos"
    __table_args__ = (
        Index("ix_plant_photos_plant_id", "plant_id"),
        Index("ix_plant_photos_photo_type", "photo_type"),
        Index("ix_plant_photos_taken_at", "taken_at"),
        CheckConstraint(
            enum_check_clause(PhotoType, column_name="photo_type"),
            name="ck_plant_photos_photo_type",
        ),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(
        BIGINT_SQL, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    photo_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=PhotoType.ROUTINE.value,
        server_default=text(f"'{PhotoType.ROUTINE.value}'"),
    )
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    taken_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    plant = relationship("Plant", back_populates="photos")


class WateringLog(Base, TimestampMixin):
    __tablename__ = "watering_logs"
    __table_args__ = (
        Index("ix_watering_logs_plant_id", "plant_id"),
        Index("ix_watering_logs_watered_at", "watered_at"),
        CheckConstraint(
            "quantity_ml IS NULL OR quantity_ml >= 0",
            name="ck_watering_logs_quantity_ml_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(
        BIGINT_SQL, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False
    )
    watered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    quantity_ml: Mapped[int | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    plant = relationship("Plant", back_populates="watering_logs")


class FertilizationLog(Base, TimestampMixin):
    __tablename__ = "fertilization_logs"
    __table_args__ = (
        Index("ix_fertilization_logs_plant_id", "plant_id"),
        Index("ix_fertilization_logs_fertilized_at", "fertilized_at"),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(
        BIGINT_SQL, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False
    )
    fertilized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    product_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    plant = relationship("Plant", back_populates="fertilization_logs")


class MaintenanceTask(Base, TimestampMixin):
    __tablename__ = "maintenance_tasks"
    __table_args__ = (
        Index("ix_maintenance_tasks_plant_id", "plant_id"),
        Index("ix_maintenance_tasks_due_at", "due_at"),
        Index("ix_maintenance_tasks_status", "status"),
        CheckConstraint(
            enum_check_clause(MaintenanceTaskStatus, column_name="status"),
            name="ck_maintenance_tasks_status",
        ),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(
        BIGINT_SQL, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=MaintenanceTaskStatus.PENDING.value,
        server_default=text(f"'{MaintenanceTaskStatus.PENDING.value}'"),
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    plant = relationship("Plant", back_populates="maintenance_tasks")


class ClimateSnapshot(Base):
    __tablename__ = "climate_snapshots"
    __table_args__ = (
        Index("ix_climate_snapshots_plant_id", "plant_id"),
        Index("ix_climate_snapshots_city_name", "city_name"),
        Index("ix_climate_snapshots_recorded_at", "recorded_at"),
        CheckConstraint(
            "humidity_percent IS NULL OR (humidity_percent >= 0 AND humidity_percent <= 100)",
            name="ck_climate_snapshots_humidity_percent_range",
        ),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    plant_id: Mapped[int | None] = mapped_column(
        BIGINT_SQL, ForeignKey("plants.id", ondelete="CASCADE"), nullable=True
    )
    city_name: Mapped[str] = mapped_column(String(150), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    temperature_c: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    humidity_percent: Mapped[int | None] = mapped_column(nullable=True)
    rain_mm: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    feels_like_c: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    uv_index: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    plant = relationship("Plant", back_populates="climate_snapshots")


class AIConversation(Base, TimestampMixin):
    __tablename__ = "ai_conversations"
    __table_args__ = (
        Index("ix_ai_conversations_user_id", "user_id"),
        Index("ix_ai_conversations_plant_id", "plant_id"),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_SQL, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[int | None] = mapped_column(
        BIGINT_SQL, ForeignKey("plants.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(180), nullable=True)

    user = relationship("User", back_populates="ai_conversations")
    plant = relationship("Plant", back_populates="ai_conversations")
    messages = relationship(
        "AIMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AIMessage(Base):
    __tablename__ = "ai_messages"
    __table_args__ = (
        Index("ix_ai_messages_conversation_id", "conversation_id"),
        Index("ix_ai_messages_created_at", "created_at"),
        CheckConstraint(
            enum_check_clause(AIMessageRole, column_name="role"),
            name="ck_ai_messages_role",
        ),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BIGINT_SQL,
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AIMessageRole.USER.value,
        server_default=text(f"'{AIMessageRole.USER.value}'"),
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    conversation = relationship("AIConversation", back_populates="messages")


class PlantDiagnosis(Base):
    __tablename__ = "plant_diagnoses"
    __table_args__ = (
        Index("ix_plant_diagnoses_plant_id", "plant_id"),
        Index("ix_plant_diagnoses_source", "source"),
        Index("ix_plant_diagnoses_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(
        BIGINT_SQL, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    plant = relationship("Plant", back_populates="diagnoses")
