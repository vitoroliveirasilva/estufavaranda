"""add auth rate limit events

Revision ID: 20260424_0002
Revises: 20260423_0001
Create Date: 2026-04-24 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260424_0002"
down_revision = "20260423_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_rate_limit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("scope_key", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "action <> ''",
            name="ck_auth_rate_limit_events_action_not_blank",
        ),
        sa.CheckConstraint(
            "scope_key <> ''",
            name="ck_auth_rate_limit_events_scope_key_not_blank",
        ),
    )
    op.create_index(
        "ix_auth_rate_limit_events_action",
        "auth_rate_limit_events",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_auth_rate_limit_events_scope_key",
        "auth_rate_limit_events",
        ["scope_key"],
        unique=False,
    )
    op.create_index(
        "ix_auth_rate_limit_events_created_at",
        "auth_rate_limit_events",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_auth_rate_limit_events_action_scope_created_at",
        "auth_rate_limit_events",
        ["action", "scope_key", "created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_auth_rate_limit_events_action_scope_created_at",
        table_name="auth_rate_limit_events",
    )
    op.drop_index(
        "ix_auth_rate_limit_events_created_at",
        table_name="auth_rate_limit_events",
    )
    op.drop_index(
        "ix_auth_rate_limit_events_scope_key",
        table_name="auth_rate_limit_events",
    )
    op.drop_index(
        "ix_auth_rate_limit_events_action",
        table_name="auth_rate_limit_events",
    )
    op.drop_table("auth_rate_limit_events")
