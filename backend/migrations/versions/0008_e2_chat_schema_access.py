"""Grant runtime role access to the chat schema."""

from collections.abc import Sequence

from alembic import op

revision: str = "0008_e2_chat_schema_access"
down_revision: str | Sequence[str] | None = "0007_e2_conversations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


SCHEMA = "chat"
TABLES = ("conversations", "messages")


def upgrade() -> None:
    op.execute(f"GRANT USAGE ON SCHEMA {SCHEMA} TO novo_runtime")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {SCHEMA} TO novo_runtime"
    )
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {SCHEMA} "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO novo_runtime"
    )


def downgrade() -> None:
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {SCHEMA} "
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM novo_runtime"
    )
    op.execute(
        f"REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {SCHEMA} FROM novo_runtime"
    )
    op.execute(f"REVOKE USAGE ON SCHEMA {SCHEMA} FROM novo_runtime")


