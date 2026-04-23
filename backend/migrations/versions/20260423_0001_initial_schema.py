"""initial schema

Revision ID: 20260423_0001
Revises: 
Create Date: 2026-04-23 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "20260423_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "species_profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("common_name", sa.String(length=150), nullable=False),
        sa.Column("scientific_name", sa.String(length=180), nullable=True),
        sa.Column("light_preference", sa.String(length=50), nullable=True),
        sa.Column("watering_frequency_days", sa.Integer(), nullable=True),
        sa.Column("ideal_humidity_min", sa.Integer(), nullable=True),
        sa.Column("ideal_humidity_max", sa.Integer(), nullable=True),
        sa.Column("ideal_temp_min", sa.Numeric(5, 2), nullable=True),
        sa.Column("ideal_temp_max", sa.Numeric(5, 2), nullable=True),
        sa.Column("substrate_notes", sa.Text(), nullable=True),
        sa.Column("general_notes", sa.Text(), nullable=True),
        sa.Column("common_symptoms", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_species_profiles_common_name", "species_profiles", ["common_name"], unique=False)
    op.create_index("ix_species_profiles_scientific_name", "species_profiles", ["scientific_name"], unique=False)

    op.create_table(
        "login_attempts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_login_attempts_email", "login_attempts", ["email"], unique=False)
    op.create_index("ix_login_attempts_ip", "login_attempts", ["ip"], unique=False)
    op.create_index("ix_login_attempts_created_at", "login_attempts", ["created_at"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("device_name", sa.String(length=120), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"], unique=False)

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),
    )

    op.create_table(
        "devices",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_name", sa.String(length=120), nullable=True),
        sa.Column("platform", sa.String(length=30), nullable=False),
        sa.Column("push_token", sa.Text(), nullable=True),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_devices_user_id", "devices", ["user_id"], unique=False)

    op.create_table(
        "plants",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("species_profile_id", sa.BigInteger(), sa.ForeignKey("species_profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("nickname", sa.String(length=150), nullable=True),
        sa.Column("acquisition_date", sa.Date(), nullable=True),
        sa.Column("environment", sa.String(length=50), nullable=True),
        sa.Column("light_exposure", sa.String(length=50), nullable=True),
        sa.Column("ventilation", sa.String(length=50), nullable=True),
        sa.Column("vase_description", sa.String(length=150), nullable=True),
        sa.Column("substrate_description", sa.String(length=150), nullable=True),
        sa.Column("location_label", sa.String(length=150), nullable=True),
        sa.Column("city_name", sa.String(length=150), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("health_status", sa.String(length=50), nullable=False, server_default="attention"),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_plants_user_id", "plants", ["user_id"], unique=False)
    op.create_index("ix_plants_species_profile_id", "plants", ["species_profile_id"], unique=False)
    op.create_index("ix_plants_health_status", "plants", ["health_status"], unique=False)
    op.create_index("ix_plants_city_name", "plants", ["city_name"], unique=False)

    op.create_table(
        "plant_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("plant_id", sa.BigInteger(), sa.ForeignKey("plants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_plant_events_plant_id", "plant_events", ["plant_id"], unique=False)
    op.create_index("ix_plant_events_event_type", "plant_events", ["event_type"], unique=False)
    op.create_index("ix_plant_events_occurred_at", "plant_events", ["occurred_at"], unique=False)

    op.create_table(
        "plant_photos",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("plant_id", sa.BigInteger(), sa.ForeignKey("plants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("original_file_name", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("photo_type", sa.String(length=30), nullable=False, server_default="routine"),
        sa.Column("caption", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_plant_photos_plant_id", "plant_photos", ["plant_id"], unique=False)
    op.create_index("ix_plant_photos_photo_type", "plant_photos", ["photo_type"], unique=False)
    op.create_index("ix_plant_photos_taken_at", "plant_photos", ["taken_at"], unique=False)

    op.create_table(
        "watering_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("plant_id", sa.BigInteger(), sa.ForeignKey("plants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("watered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quantity_ml", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_watering_logs_plant_id", "watering_logs", ["plant_id"], unique=False)
    op.create_index("ix_watering_logs_watered_at", "watering_logs", ["watered_at"], unique=False)

    op.create_table(
        "fertilization_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("plant_id", sa.BigInteger(), sa.ForeignKey("plants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fertilized_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("product_name", sa.String(length=150), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "maintenance_tasks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("plant_id", sa.BigInteger(), sa.ForeignKey("plants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'done', 'canceled')", name="ck_maintenance_tasks_status"),
    )

    op.create_table(
        "climate_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("plant_id", sa.BigInteger(), sa.ForeignKey("plants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("city_name", sa.String(length=150), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature_c", sa.Numeric(5, 2), nullable=True),
        sa.Column("humidity_percent", sa.Integer(), nullable=True),
        sa.Column("rain_mm", sa.Numeric(8, 2), nullable=True),
        sa.Column("feels_like_c", sa.Numeric(5, 2), nullable=True),
        sa.Column("uv_index", sa.Numeric(5, 2), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_climate_snapshots_plant_id", "climate_snapshots", ["plant_id"], unique=False)
    op.create_index("ix_climate_snapshots_city_name", "climate_snapshots", ["city_name"], unique=False)
    op.create_index("ix_climate_snapshots_recorded_at", "climate_snapshots", ["recorded_at"], unique=False)

    op.create_table(
        "notification_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", sa.BigInteger(), sa.ForeignKey("plants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("dedupe_key", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discarded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notification_events_user_id", "notification_events", ["user_id"], unique=False)
    op.create_index("ix_notification_events_plant_id", "notification_events", ["plant_id"], unique=False)
    op.create_index("ix_notification_events_status", "notification_events", ["status"], unique=False)
    op.create_index("ix_notification_events_dedupe_key", "notification_events", ["dedupe_key"], unique=True)

    op.create_table(
        "notification_dispatches",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("notification_event_id", sa.BigInteger(), sa.ForeignKey("notification_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("provider_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", sa.BigInteger(), sa.ForeignKey("plants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "ai_messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.BigInteger(), sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('system', 'user', 'assistant')", name="ck_ai_messages_role"),
    )

    op.create_table(
        "plant_diagnoses",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("plant_id", sa.BigInteger(), sa.ForeignKey("plants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.String(length=20), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("plant_diagnoses")
    op.drop_table("ai_messages")
    op.drop_table("ai_conversations")
    op.drop_table("notification_dispatches")
    op.drop_index("ix_notification_events_dedupe_key", table_name="notification_events")
    op.drop_index("ix_notification_events_status", table_name="notification_events")
    op.drop_index("ix_notification_events_plant_id", table_name="notification_events")
    op.drop_index("ix_notification_events_user_id", table_name="notification_events")
    op.drop_table("notification_events")
    op.drop_index("ix_climate_snapshots_recorded_at", table_name="climate_snapshots")
    op.drop_index("ix_climate_snapshots_city_name", table_name="climate_snapshots")
    op.drop_index("ix_climate_snapshots_plant_id", table_name="climate_snapshots")
    op.drop_table("climate_snapshots")
    op.drop_table("maintenance_tasks")
    op.drop_table("fertilization_logs")
    op.drop_index("ix_watering_logs_watered_at", table_name="watering_logs")
    op.drop_index("ix_watering_logs_plant_id", table_name="watering_logs")
    op.drop_table("watering_logs")
    op.drop_index("ix_plant_photos_taken_at", table_name="plant_photos")
    op.drop_index("ix_plant_photos_photo_type", table_name="plant_photos")
    op.drop_index("ix_plant_photos_plant_id", table_name="plant_photos")
    op.drop_table("plant_photos")
    op.drop_index("ix_plant_events_occurred_at", table_name="plant_events")
    op.drop_index("ix_plant_events_event_type", table_name="plant_events")
    op.drop_index("ix_plant_events_plant_id", table_name="plant_events")
    op.drop_table("plant_events")
    op.drop_index("ix_plants_city_name", table_name="plants")
    op.drop_index("ix_plants_health_status", table_name="plants")
    op.drop_index("ix_plants_species_profile_id", table_name="plants")
    op.drop_index("ix_plants_user_id", table_name="plants")
    op.drop_table("plants")
    op.drop_index("ix_devices_user_id", table_name="devices")
    op.drop_table("devices")
    op.drop_table("password_reset_tokens")
    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_login_attempts_created_at", table_name="login_attempts")
    op.drop_index("ix_login_attempts_ip", table_name="login_attempts")
    op.drop_index("ix_login_attempts_email", table_name="login_attempts")
    op.drop_table("login_attempts")
    op.drop_index("ix_species_profiles_scientific_name", table_name="species_profiles")
    op.drop_index("ix_species_profiles_common_name", table_name="species_profiles")
    op.drop_table("species_profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
