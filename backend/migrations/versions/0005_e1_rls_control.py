"""Enable RLS on owner-scoped control tables."""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_e1_rls_control"
down_revision: str | Sequence[str] | None = "0004_e1_transport_security"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNER_CONTEXT_SQL = "NULLIF(current_setting('app.owner_id', true), '')::uuid"


def upgrade() -> None:
    op.execute("ALTER TABLE governance.system_control_state ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE governance.system_control_state FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY system_control_state_owner_policy ON governance.system_control_state "
        f"USING (owner_id = {OWNER_CONTEXT_SQL}) WITH CHECK (owner_id = {OWNER_CONTEXT_SQL})"
    )

    op.execute("ALTER TABLE governance.control_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE governance.control_events FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY control_events_owner_select ON governance.control_events "
        f"FOR SELECT USING (owner_id = {OWNER_CONTEXT_SQL})"
    )
    op.execute(
        f"CREATE POLICY control_events_owner_insert ON governance.control_events "
        f"FOR INSERT WITH CHECK (owner_id = {OWNER_CONTEXT_SQL})"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS control_events_owner_insert ON governance.control_events")
    op.execute("DROP POLICY IF EXISTS control_events_owner_select ON governance.control_events")
    op.execute("ALTER TABLE governance.control_events NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE governance.control_events DISABLE ROW LEVEL SECURITY")

    op.execute(
        "DROP POLICY IF EXISTS system_control_state_owner_policy ON governance.system_control_state"
    )
    op.execute("ALTER TABLE governance.system_control_state NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE governance.system_control_state DISABLE ROW LEVEL SECURITY")
