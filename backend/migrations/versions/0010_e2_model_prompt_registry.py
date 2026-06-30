"""Create model and prompt registry tables."""

# ruff: noqa: E501

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0010_e2_model_prompt_registry"
down_revision: str | Sequence[str] | None = "0009_e2_response_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MODEL_FAST_ID = uuid4()
MODEL_DEEP_ID = uuid4()
MODEL_ECHO_ID = uuid4()
PROMPT_TEMPLATE_ID = uuid4()
PROMPT_CONTENT = (
    "You are NOVO, the owner-first AI OS. Respond calmly, directly, and helpfully. "
    "Write in plain text with short paragraphs. If you use headings, put them on their own line "
    "without markdown symbols like ### or **. Use simple hyphen bullets only when helpful. "
    "Avoid dense markdown formatting unless the user explicitly asks for it."
)
PROMPT_CONTENT_HASH = sha256(PROMPT_CONTENT.encode("utf-8")).hexdigest()
PROMPT_VERSION_ID = uuid4()
PROMPT_BINDING_ID = uuid4()
PROMPT_ACTIVATED_AT = datetime.now(UTC)
PROMPT_VALID_FROM = datetime.now(UTC)


def upgrade() -> None:
    op.execute(sa.text('CREATE SCHEMA IF NOT EXISTS "platform"'))
    op.create_table(
        "model_catalog",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model_key", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column(
            "capabilities",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("context_window", sa.Integer(), nullable=False),
        sa.Column("max_output_tokens", sa.Integer(), nullable=False),
        sa.Column(
            "privacy_eligibility",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'private'"),
        ),
        sa.Column(
            "pricing",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.UniqueConstraint(
            "provider", "model_key", name="uq_platform_model_catalog_provider_model_key"
        ),
        schema="platform",
    )
    op.create_index(
        "ix_platform_model_catalog_enabled", "model_catalog", ["enabled"], schema="platform"
    )

    op.create_table(
        "model_policies",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "rules",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "max_classification",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'private'"),
        ),
        sa.Column("max_cost_minor", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "currency", sa.String(length=16), nullable=False, server_default=sa.text("'USD'")
        ),
        sa.Column(
            "latency_target_ms", sa.Integer(), nullable=False, server_default=sa.text("5000")
        ),
        sa.Column("fallback_allowed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        schema="platform",
    )
    op.create_index(
        "ix_platform_model_policies_owner_enabled",
        "model_policies",
        ["owner_id", "enabled"],
        schema="platform",
    )

    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prompt_key", sa.String(length=120), nullable=False),
        sa.Column("purpose", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column(
            "variable_schema",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "security_level",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'private'"),
        ),
        sa.Column(
            "owner_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
        sa.UniqueConstraint("prompt_key", name="uq_platform_prompt_templates_prompt_key"),
        schema="platform",
    )
    op.create_index(
        "ix_platform_prompt_templates_purpose", "prompt_templates", ["purpose"], schema="platform"
    )

    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "template_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform.prompt_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "status", sa.String(length=24), nullable=False, server_default=sa.text("'draft'")
        ),
        sa.Column("change_reason", sa.String(length=500), nullable=True),
        sa.Column(
            "created_by",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "evaluation_status",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "template_id", "version_no", name="uq_platform_prompt_versions_template_version"
        ),
        schema="platform",
    )
    op.create_index(
        "ix_platform_prompt_versions_template_status",
        "prompt_versions",
        ["template_id", "status"],
        schema="platform",
    )
    op.create_index(
        "ix_platform_prompt_versions_content_hash",
        "prompt_versions",
        ["content_hash"],
        schema="platform",
    )

    op.create_table(
        "prompt_bindings",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("purpose", sa.String(length=120), nullable=False),
        sa.Column("agent_type", sa.String(length=120), nullable=True),
        sa.Column("tool_capability_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "prompt_version_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform.prompt_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        schema="platform",
    )
    op.create_index(
        "ix_platform_prompt_bindings_scope",
        "prompt_bindings",
        ["owner_id", "purpose", "agent_type"],
        schema="platform",
    )
    op.create_index(
        "uq_platform_prompt_bindings_active_scope",
        "prompt_bindings",
        ["owner_id", "purpose", "agent_type", "tool_capability_id"],
        schema="platform",
        unique=True,
        postgresql_where=sa.text("valid_until IS NULL"),
    )

    op.bulk_insert(
        sa.table(
            "model_catalog",
            sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
            sa.column("provider", sa.String()),
            sa.column("model_key", sa.String()),
            sa.column("display_name", sa.String()),
            sa.column("capabilities", sa.dialects.postgresql.JSONB()),
            sa.column("context_window", sa.Integer()),
            sa.column("max_output_tokens", sa.Integer()),
            sa.column("privacy_eligibility", sa.String()),
            sa.column("pricing", sa.dialects.postgresql.JSONB()),
            sa.column("enabled", sa.Boolean()),
            schema="platform",
        ),
        [
            {
                "id": MODEL_FAST_ID,
                "provider": "openrouter",
                "model_key": "openrouter/free/fast",
                "display_name": "OpenRouter Free Fast",
                "capabilities": {"fast_path": True, "streaming": True, "structured_output": True},
                "context_window": 8192,
                "max_output_tokens": 2048,
                "privacy_eligibility": "private",
                "pricing": {"input_minor": 0, "output_minor": 0, "currency": "USD"},
                "enabled": True,
            },
            {
                "id": MODEL_DEEP_ID,
                "provider": "openrouter",
                "model_key": "openrouter/free/deep",
                "display_name": "OpenRouter Free Deep",
                "capabilities": {"fast_path": False, "deep_reasoning": True, "streaming": True},
                "context_window": 32768,
                "max_output_tokens": 4096,
                "privacy_eligibility": "private",
                "pricing": {"input_minor": 0, "output_minor": 0, "currency": "USD"},
                "enabled": True,
            },
            {
                "id": MODEL_ECHO_ID,
                "provider": "stub",
                "model_key": "stub/echo",
                "display_name": "Stub Echo",
                "capabilities": {"fast_path": True, "streaming": True},
                "context_window": 4096,
                "max_output_tokens": 1024,
                "privacy_eligibility": "public",
                "pricing": {"input_minor": 0, "output_minor": 0, "currency": "USD"},
                "enabled": True,
            },
        ],
    )

    op.bulk_insert(
        sa.table(
            "prompt_templates",
            sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
            sa.column("prompt_key", sa.String()),
            sa.column("purpose", sa.String()),
            sa.column("name", sa.String()),
            sa.column("description", sa.String()),
            sa.column("variable_schema", sa.dialects.postgresql.JSONB()),
            sa.column("security_level", sa.String()),
            sa.column("owner_id", sa.dialects.postgresql.UUID(as_uuid=True)),
            schema="platform",
        ),
        [
            {
                "id": PROMPT_TEMPLATE_ID,
                "prompt_key": "conversation.reply",
                "purpose": "conversation.reply",
                "name": "Conversation reply",
                "description": "Default NOVO fast-path prompt for assistant chat replies.",
                "variable_schema": {
                    "type": "object",
                    "properties": {
                        "owner_name": {"type": "string"},
                        "conversation_title": {"type": "string"},
                        "message": {"type": "string"},
                    },
                    "required": ["message"],
                    "additionalProperties": False,
                },
                "security_level": "private",
                "owner_id": None,
            }
        ],
    )

    op.bulk_insert(
        sa.table(
            "prompt_versions",
            sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
            sa.column("template_id", sa.dialects.postgresql.UUID(as_uuid=True)),
            sa.column("version_no", sa.Integer()),
            sa.column("content", sa.Text()),
            sa.column("content_hash", sa.String()),
            sa.column("status", sa.String()),
            sa.column("change_reason", sa.String()),
            sa.column("created_by", sa.dialects.postgresql.UUID(as_uuid=True)),
            sa.column("evaluation_status", sa.String()),
            sa.column("activated_at", sa.DateTime(timezone=True)),
            sa.column("retired_at", sa.DateTime(timezone=True)),
            schema="platform",
        ),
        [
            {
                "id": PROMPT_VERSION_ID,
                "template_id": PROMPT_TEMPLATE_ID,
                "version_no": 1,
                "content": PROMPT_CONTENT,
                "content_hash": PROMPT_CONTENT_HASH,
                "status": "active",
                "change_reason": "Initial fast-path prompt seed",
                "created_by": None,
                "evaluation_status": "passed",
                "activated_at": PROMPT_ACTIVATED_AT,
                "retired_at": None,
            }
        ],
    )

    op.bulk_insert(
        sa.table(
            "prompt_bindings",
            sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
            sa.column("owner_id", sa.dialects.postgresql.UUID(as_uuid=True)),
            sa.column("purpose", sa.String()),
            sa.column("agent_type", sa.String()),
            sa.column("tool_capability_id", sa.dialects.postgresql.UUID(as_uuid=True)),
            sa.column("prompt_version_id", sa.dialects.postgresql.UUID(as_uuid=True)),
            sa.column("priority", sa.Integer()),
            sa.column("valid_from", sa.DateTime(timezone=True)),
            sa.column("valid_until", sa.DateTime(timezone=True)),
            schema="platform",
        ),
        [
            {
                "id": PROMPT_BINDING_ID,
                "owner_id": None,
                "purpose": "conversation.reply",
                "agent_type": None,
                "tool_capability_id": None,
                "prompt_version_id": PROMPT_VERSION_ID,
                "priority": 1,
                "valid_from": PROMPT_VALID_FROM,
                "valid_until": None,
            }
        ],
    )

    op.execute("GRANT USAGE ON SCHEMA platform TO novo_runtime")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA platform TO novo_runtime"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA platform GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO novo_runtime"
    )


def downgrade() -> None:
    op.drop_table("prompt_bindings", schema="platform")
    op.drop_table("prompt_versions", schema="platform")
    op.drop_table("prompt_templates", schema="platform")
    op.drop_table("model_policies", schema="platform")
    op.drop_table("model_catalog", schema="platform")
    op.execute("DROP SCHEMA IF EXISTS platform")
