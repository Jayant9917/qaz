"""Create runtime role and grant privileges for RLS enforcement."""

from collections.abc import Sequence

from alembic import op

revision: str = "0006_e1_runtime_role"
down_revision: str | Sequence[str] | None = "0005_e1_rls_control"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


SCHEMAS = ("identity", "governance", "audit", "chat")
TABLES = {
    "identity": ("roles", "sessions", "users", "user_roles"),
    "governance": ("control_events", "permissions", "role_permissions", "system_control_state"),
    "audit": ("audit_logs",),
}


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'novo_runtime') THEN
                CREATE ROLE novo_runtime NOLOGIN NOBYPASSRLS NOSUPERUSER;
            END IF;
        END $$;
        """
    )
    op.execute("GRANT novo_runtime TO novo")

    for schema in SCHEMAS:
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO novo_runtime")
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} "
            "TO novo_runtime"
        )
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} "
            "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO novo_runtime"
        )


def downgrade() -> None:
    for schema in SCHEMAS:
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} "
            "REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM novo_runtime"
        )
        op.execute(
            f"REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} "
            "FROM novo_runtime"
        )
        op.execute(f"REVOKE USAGE ON SCHEMA {schema} FROM novo_runtime")

    op.execute("REVOKE novo_runtime FROM novo")
    op.execute("DROP ROLE IF EXISTS novo_runtime")

