"""Create E2 conversation and message tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_e2_conversations"
down_revision: str | Sequence[str] | None = "0006_e1_runtime_role"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column(
            "status", sa.String(length=24), nullable=False, server_default=sa.text("'active'")
        ),
        sa.Column(
            "classification",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'private'"),
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("summary_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "default_model_policy_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
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
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.UniqueConstraint("owner_id", "title", name="uq_chat_conversations_owner_title"),
        schema="chat",
    )
    op.create_index(
        "ix_chat_conversations_owner_id",
        "conversations",
        ["owner_id"],
        unique=False,
        schema="chat",
    )
    op.create_index(
        "ix_chat_conversations_owner_updated_at",
        "conversations",
        ["owner_id", "updated_at"],
        unique=False,
        schema="chat",
    )

    op.create_table(
        "messages",
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
            "parent_message_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat.messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("sequence_no", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=24), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "content_format",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'text/plain'"),
        ),
        sa.Column(
            "classification",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'private'"),
        ),
        sa.Column(
            "status", sa.String(length=24), nullable=False, server_default=sa.text("'created'")
        ),
        sa.Column("model_call_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tool_action_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "metadata",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("conversation_id", "sequence_no", name="uq_chat_messages_sequence"),
        schema="chat",
    )
    op.create_index(
        "ix_chat_messages_owner_id",
        "messages",
        ["owner_id"],
        unique=False,
        schema="chat",
    )
    op.create_index(
        "ix_chat_messages_conversation_id",
        "messages",
        ["conversation_id"],
        unique=False,
        schema="chat",
    )
    op.create_index(
        "ix_chat_messages_conversation_sequence",
        "messages",
        ["conversation_id", "sequence_no"],
        unique=False,
        schema="chat",
    )
    op.create_index(
        "ix_chat_messages_owner_created_at",
        "messages",
        ["owner_id", "created_at"],
        unique=False,
        schema="chat",
    )
    op.create_index(
        "ix_chat_messages_parent_message_id",
        "messages",
        ["parent_message_id"],
        unique=False,
        schema="chat",
    )


def downgrade() -> None:
    op.drop_index("ix_chat_messages_parent_message_id", table_name="messages", schema="chat")
    op.drop_index("ix_chat_messages_owner_created_at", table_name="messages", schema="chat")
    op.drop_index("ix_chat_messages_conversation_sequence", table_name="messages", schema="chat")
    op.drop_index("ix_chat_messages_conversation_id", table_name="messages", schema="chat")
    op.drop_index("ix_chat_messages_owner_id", table_name="messages", schema="chat")
    op.drop_table("messages", schema="chat")

    op.drop_index(
        "ix_chat_conversations_owner_updated_at", table_name="conversations", schema="chat"
    )
    op.drop_index("ix_chat_conversations_owner_id", table_name="conversations", schema="chat")
    op.drop_table("conversations", schema="chat")


