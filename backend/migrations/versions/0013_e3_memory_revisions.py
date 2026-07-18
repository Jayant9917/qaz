"""Add immutable memory revision snapshots."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_e3_memory_revisions"
down_revision: str | Sequence[str] | None = "0012_e3_memory_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memory_revisions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "memory_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("memory.memories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("canonical_content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("source_type", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        schema="memory",
    )
    op.create_index(
        "ix_memory_revisions_owner_memory_created_at",
        "memory_revisions",
        ["owner_id", "memory_id", "created_at"],
        schema="memory",
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON memory.memory_revisions TO novo_runtime")
    op.execute("ALTER TABLE memory.memory_revisions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE memory.memory_revisions FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY memory_revisions_owner_policy ON memory.memory_revisions "
        "USING (owner_id = NULLIF(current_setting('app.owner_id', true), '')::uuid) "
        "WITH CHECK (owner_id = NULLIF(current_setting('app.owner_id', true), '')::uuid)"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS memory_revisions_owner_policy ON memory.memory_revisions")
    op.execute("ALTER TABLE memory.memory_revisions NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE memory.memory_revisions DISABLE ROW LEVEL SECURITY")
    op.execute("REVOKE SELECT, INSERT, UPDATE, DELETE ON memory.memory_revisions FROM novo_runtime")
    op.drop_index(
        "ix_memory_revisions_owner_memory_created_at",
        table_name="memory_revisions",
        schema="memory",
    )
    op.drop_table("memory_revisions", schema="memory")
