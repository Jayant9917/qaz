"""Add model call accounting table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_e2_model_calls"
down_revision = "0010_e2_model_prompt_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_calls",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("agent_run_id", sa.UUID(), nullable=True),
        sa.Column("message_id", sa.UUID(), nullable=True),
        sa.Column("model_id", sa.UUID(), nullable=False),
        sa.Column("route_reason", sa.String(length=240), nullable=False),
        sa.Column(
            "classification_max",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'private'"),
        ),
        sa.Column("provider_request_id", sa.String(length=120), nullable=True),
        sa.Column(
            "status",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'running'"),
        ),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("cached_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cost_minor", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "currency",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'USD'"),
        ),
        sa.Column("prompt_hash", sa.String(length=64), nullable=False),
        sa.Column("response_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=48), nullable=True),
        sa.Column("error_detail_safe", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["identity.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_id"], ["platform.model_catalog.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["message_id"], ["chat.messages.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "input_tokens >= 0",
            name="ck_platform_model_calls_input_tokens_nonnegative",
        ),
        sa.CheckConstraint(
            "output_tokens >= 0",
            name="ck_platform_model_calls_output_tokens_nonnegative",
        ),
        sa.CheckConstraint(
            "cached_tokens >= 0",
            name="ck_platform_model_calls_cached_tokens_nonnegative",
        ),
        sa.CheckConstraint(
            "cost_minor >= 0",
            name="ck_platform_model_calls_cost_minor_nonnegative",
        ),
        sa.CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="ck_platform_model_calls_latency_ms_nonnegative",
        ),
        sa.CheckConstraint(
            "classification_max IN ('public', 'private', 'confidential', 'secret', 'restricted')",
            name="ck_platform_model_calls_classification_max_allowed",
        ),
        schema="platform",
    )
    op.create_index(
        "ix_platform_model_calls_owner_started_at",
        "model_calls",
        ["owner_id", "started_at"],
        schema="platform",
    )
    op.create_index(
        "ix_platform_model_calls_model_started_at",
        "model_calls",
        ["model_id", "started_at"],
        schema="platform",
    )
    op.create_index(
        "ix_platform_model_calls_message_id",
        "model_calls",
        ["message_id"],
        schema="platform",
    )
    op.create_index(
        "ix_platform_model_calls_provider_request_id",
        "model_calls",
        ["provider_request_id"],
        schema="platform",
    )
    op.execute("GRANT USAGE ON SCHEMA platform TO novo_runtime")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA platform TO novo_runtime"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA platform GRANT SELECT, INSERT, UPDATE, DELETE "
        "ON TABLES TO novo_runtime"
    )


def downgrade() -> None:
    op.drop_index(
        "ix_platform_model_calls_provider_request_id",
        table_name="model_calls",
        schema="platform",
    )
    op.drop_index(
        "ix_platform_model_calls_message_id",
        table_name="model_calls",
        schema="platform",
    )
    op.drop_index(
        "ix_platform_model_calls_model_started_at",
        table_name="model_calls",
        schema="platform",
    )
    op.drop_index(
        "ix_platform_model_calls_owner_started_at",
        table_name="model_calls",
        schema="platform",
    )
    op.drop_table("model_calls", schema="platform")
