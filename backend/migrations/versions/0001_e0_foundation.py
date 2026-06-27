"""Create NOVO schemas and migration metadata.

Revision ID: 0001_e0
Revises:
Create Date: 2026-06-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_e0"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMAS = (
    "identity",
    "chat",
    "memory",
    "knowledge",
    "agent",
    "governance",
    "automation",
    "platform",
    "audit",
)


def upgrade() -> None:
    for schema in SCHEMAS:
        op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))

    op.create_table(
        "schema_metadata",
        sa.Column("key", sa.String(length=120), primary_key=True),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        schema="platform",
    )
    metadata_table = sa.table(
        "schema_metadata",
        sa.column("key", sa.String),
        sa.column("value", sa.String),
        schema="platform",
    )
    op.bulk_insert(metadata_table, [{"key": "foundation_version", "value": "e0"}])


def downgrade() -> None:
    op.drop_table("schema_metadata", schema="platform")
    for schema in reversed(SCHEMAS):
        op.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}"'))
