"""Create E1 control-state and user settings tables/columns.

Revision ID: 0003_e1_control
Revises: 0002_e1_auth
Create Date: 2026-06-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_e1_control"
down_revision: str | Sequence[str] | None = "0002_e1_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "timezone", sa.String(length=64), nullable=False, server_default=sa.text("'UTC'")
        ),
        schema="identity",
    )
    op.add_column(
        "users",
        sa.Column("locale", sa.String(length=16), nullable=False, server_default=sa.text("'en'")),
        schema="identity",
    )
    op.add_column(
        "users",
        sa.Column(
            "status", sa.String(length=24), nullable=False, server_default=sa.text("'active'")
        ),
        schema="identity",
    )
    op.add_column(
        "users",
        sa.Column(
            "security_mode",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'assistant'"),
        ),
        schema="identity",
    )
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        schema="identity",
    )
    op.add_column(
        "users",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        schema="identity",
    )
    op.add_column(
        "users",
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        schema="identity",
    )
    op.create_index(
        "ix_identity_users_status", "users", ["status"], unique=False, schema="identity"
    )

    op.create_table(
        "system_control_state",
        sa.Column(
            "owner_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "kill_switch_active", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "automations_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("tools_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "external_models_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "security_mode",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'assistant'"),
        ),
        sa.Column(
            "changed_by",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("change_reason", sa.String(length=500), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        schema="governance",
    )

    op.create_table(
        "control_events",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "owner_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("control_name", sa.String(length=120), nullable=False),
        sa.Column("previous_value", sa.String(length=2000), nullable=True),
        sa.Column("new_value", sa.String(length=2000), nullable=True),
        sa.Column(
            "actor_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("trace_id", sa.String(length=128), nullable=True),
        schema="governance",
    )
    op.create_index(
        "ix_governance_control_events_owner_id", "control_events", ["owner_id"], schema="governance"
    )
    op.create_index(
        "ix_governance_control_events_control_name",
        "control_events",
        ["control_name"],
        schema="governance",
    )
    op.create_index(
        "ix_governance_control_events_created_at",
        "control_events",
        ["created_at"],
        schema="governance",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_governance_control_events_created_at", table_name="control_events", schema="governance"
    )
    op.drop_index(
        "ix_governance_control_events_control_name",
        table_name="control_events",
        schema="governance",
    )
    op.drop_index(
        "ix_governance_control_events_owner_id", table_name="control_events", schema="governance"
    )
    op.drop_table("control_events", schema="governance")
    op.drop_table("system_control_state", schema="governance")
    op.drop_index("ix_identity_users_status", table_name="users", schema="identity")
    op.drop_column("users", "version", schema="identity")
    op.drop_column("users", "deleted_at", schema="identity")
    op.drop_column("users", "last_login_at", schema="identity")
    op.drop_column("users", "security_mode", schema="identity")
    op.drop_column("users", "status", schema="identity")
    op.drop_column("users", "locale", schema="identity")
    op.drop_column("users", "timezone", schema="identity")
