"""Create chat response-run table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_e2_response_runs"
down_revision: str | Sequence[str] | None = "0008_e2_chat_schema_access"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "responses",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat.conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_message_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat.messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'queued'"),
        ),
        sa.Column(
            "route",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'fast'"),
        ),
        sa.Column(
            "route_reason",
            sa.String(length=240),
            nullable=False,
            server_default=sa.text("'fast-path stub'"),
        ),
        sa.Column(
            "prompt_version",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'e2.stub.v1'"),
        ),
        sa.Column(
            "model_provider",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'stub'"),
        ),
        sa.Column(
            "model_name",
            sa.String(length=80),
            nullable=False,
            server_default=sa.text("'echo'"),
        ),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        schema="chat",
    )
    op.create_index("ix_chat_responses_owner_id", "responses", ["owner_id"], schema="chat")
    op.create_index(
        "ix_chat_responses_conversation_id",
        "responses",
        ["conversation_id"],
        schema="chat",
    )
    op.create_index(
        "ix_chat_responses_user_message_id",
        "responses",
        ["user_message_id"],
        schema="chat",
    )
    op.execute("GRANT USAGE ON SCHEMA chat TO novo_runtime")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA chat TO novo_runtime")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA chat GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES "
        "TO novo_runtime"
    )


def downgrade() -> None:
    op.drop_index("ix_chat_responses_user_message_id", table_name="responses", schema="chat")
    op.drop_index("ix_chat_responses_conversation_id", table_name="responses", schema="chat")
    op.drop_index("ix_chat_responses_owner_id", table_name="responses", schema="chat")
    op.drop_table("responses", schema="chat")
