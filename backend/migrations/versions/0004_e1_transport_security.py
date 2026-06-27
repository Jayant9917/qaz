"""Add CSRF token hashes to sessions."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_e1_transport_security"
down_revision: str | Sequence[str] | None = "0003_e1_control"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("csrf_token_hash", sa.String(length=64), nullable=True),
        schema="identity",
    )
    op.execute(
        sa.text(
            "UPDATE identity.sessions "
            "SET csrf_token_hash = md5(token_hash) "
            "WHERE csrf_token_hash IS NULL"
        )
    )
    op.alter_column(
        "sessions",
        "csrf_token_hash",
        existing_type=sa.String(length=64),
        nullable=False,
        schema="identity",
    )
    op.create_index(
        "ix_identity_sessions_csrf_token_hash",
        "sessions",
        ["csrf_token_hash"],
        unique=True,
        schema="identity",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_identity_sessions_csrf_token_hash",
        table_name="sessions",
        schema="identity",
    )
    op.drop_column("sessions", "csrf_token_hash", schema="identity")
