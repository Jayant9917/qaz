"""Create E1 identity, governance, and audit tables.

Revision ID: 0002_e1_auth
Revises: 0001_e0
Create Date: 2026-06-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_e1_auth"
down_revision: str | Sequence[str] | None = "0001_e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("key", name="uq_roles_key"),
        schema="identity",
    )
    op.create_index(
        "ix_identity_roles_key",
        "roles",
        ["key"],
        unique=False,
        schema="identity",
    )

    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
        schema="identity",
    )
    op.create_index(
        "ix_identity_users_email",
        "users",
        ["email"],
        unique=False,
        schema="identity",
    )

    op.create_table(
        "sessions",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(length=200), nullable=True),
        sa.Column("user_agent", sa.String(length=400), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
        schema="identity",
    )
    op.create_index(
        "ix_identity_sessions_user_id",
        "sessions",
        ["user_id"],
        unique=False,
        schema="identity",
    )
    op.create_index(
        "ix_identity_sessions_token_hash",
        "sessions",
        ["token_hash"],
        unique=False,
        schema="identity",
    )
    op.create_index(
        "ix_identity_sessions_expires_at",
        "sessions",
        ["expires_at"],
        unique=False,
        schema="identity",
    )

    op.create_table(
        "permissions",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("resource", sa.String(length=120), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("risk_level", sa.String(length=30), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("key", name="uq_permissions_key"),
        schema="governance",
    )
    op.create_index(
        "ix_governance_permissions_key",
        "permissions",
        ["key"],
        unique=False,
        schema="governance",
    )

    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        schema="identity",
    )

    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance.permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        schema="governance",
    )

    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "actor_user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "session_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.String(length=120), nullable=True),
        sa.Column("outcome", sa.String(length=40), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        schema="audit",
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"], schema="audit")
    op.create_index("ix_audit_logs_session_id", "audit_logs", ["session_id"], schema="audit")
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], schema="audit")
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"], schema="audit")
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"], schema="audit")
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"], schema="audit")
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], schema="audit")


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs", schema="audit")
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs", schema="audit")
    op.drop_index("ix_audit_logs_resource_id", table_name="audit_logs", schema="audit")
    op.drop_index("ix_audit_logs_resource_type", table_name="audit_logs", schema="audit")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs", schema="audit")
    op.drop_index("ix_audit_logs_session_id", table_name="audit_logs", schema="audit")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs", schema="audit")
    op.drop_table("audit_logs", schema="audit")

    op.drop_table("role_permissions", schema="governance")
    op.drop_table("user_roles", schema="identity")

    op.drop_index("ix_governance_permissions_key", table_name="permissions", schema="governance")
    op.drop_table("permissions", schema="governance")

    op.drop_index("ix_identity_sessions_expires_at", table_name="sessions", schema="identity")
    op.drop_index("ix_identity_sessions_token_hash", table_name="sessions", schema="identity")
    op.drop_index("ix_identity_sessions_user_id", table_name="sessions", schema="identity")
    op.drop_table("sessions", schema="identity")

    op.drop_index("ix_identity_users_email", table_name="users", schema="identity")
    op.drop_table("users", schema="identity")

    op.drop_index("ix_identity_roles_key", table_name="roles", schema="identity")
    op.drop_table("roles", schema="identity")