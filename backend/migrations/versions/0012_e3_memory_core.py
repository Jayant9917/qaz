"""Create the E3 explicit memory core tables."""

# ruff: noqa: E501

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0012_e3_memory_core'
down_revision: str | Sequence[str] | None = '0011_e2_model_calls'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNER_CONTEXT_SQL = "NULLIF(current_setting('app.owner_id', true), '')::uuid"


def upgrade() -> None:
    op.execute(sa.text('CREATE SCHEMA IF NOT EXISTS "memory"'))

    op.create_table(
        'memories',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'owner_id',
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey('identity.users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('kind', sa.String(length=24), nullable=False),
        sa.Column('title', sa.String(length=240), nullable=False),
        sa.Column('canonical_content', sa.Text(), nullable=False),
        sa.Column('classification', sa.String(length=24), nullable=False, server_default=sa.text("'private'")),
        sa.Column('status', sa.String(length=24), nullable=False, server_default=sa.text("'active'")),
        sa.Column('confidence', sa.Numeric(4, 3), nullable=False, server_default=sa.text('1.000')),
        sa.Column('importance', sa.Numeric(4, 3), nullable=False, server_default=sa.text('0.500')),
        sa.Column('access_count', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retention_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_after', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_type', sa.String(length=120), nullable=False, server_default=sa.text("'explicit_remember'")),
        sa.Column('source_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_locator', sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('evidence_excerpt', sa.Text(), nullable=True),
        sa.Column('evidence_hash', sa.String(length=64), nullable=False),
        sa.Column('extraction_method', sa.String(length=120), nullable=False, server_default=sa.text("'explicit'")),
        sa.Column('embedding_status', sa.String(length=24), nullable=False, server_default=sa.text("'not_requested'")),
        sa.Column('embedding_version', sa.String(length=120), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='memory_confidence_range'),
        sa.CheckConstraint('importance >= 0 AND importance <= 1', name='memory_importance_range'),
        sa.CheckConstraint(
            'valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from',
            name='memory_valid_window_order',
        ),
        schema='memory',
    )
    op.create_index('ix_memory_memories_owner_status_kind', 'memories', ['owner_id', 'status', 'kind'], schema='memory')
    op.create_index('ix_memory_memories_owner_classification', 'memories', ['owner_id', 'classification'], schema='memory')
    op.create_index('ix_memory_memories_review_after', 'memories', ['review_after'], schema='memory')
    op.create_index('ix_memory_memories_retention_until', 'memories', ['retention_until'], schema='memory')
    op.create_index('ix_memory_memories_source_type_source_id', 'memories', ['source_type', 'source_id'], schema='memory')

    op.create_table(
        'memory_access_events',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'owner_id',
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey('identity.users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'memory_id',
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey('memory.memories.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('actor_type', sa.String(length=24), nullable=False),
        sa.Column('actor_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_run_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('purpose', sa.String(length=120), nullable=False),
        sa.Column('decision', sa.String(length=24), nullable=False),
        sa.Column('policy_version_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('relevance_score', sa.Numeric(4, 3), nullable=True),
        sa.Column('used_in_prompt', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('provider', sa.String(length=80), nullable=True),
        sa.Column('trace_id', sa.String(length=80), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        schema='memory',
    )
    op.create_index('ix_memory_access_events_owner_created_at', 'memory_access_events', ['owner_id', 'created_at'], schema='memory')
    op.create_index('ix_memory_access_events_memory_created_at', 'memory_access_events', ['memory_id', 'created_at'], schema='memory')

    op.execute('GRANT USAGE ON SCHEMA memory TO novo_runtime')
    op.execute('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA memory TO novo_runtime')
    op.execute('ALTER DEFAULT PRIVILEGES IN SCHEMA memory GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO novo_runtime')

    op.execute('ALTER TABLE memory.memories ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE memory.memories FORCE ROW LEVEL SECURITY')
    op.execute(
        f'CREATE POLICY memories_owner_policy ON memory.memories '
        f'USING (owner_id = {OWNER_CONTEXT_SQL}) '
        f'WITH CHECK (owner_id = {OWNER_CONTEXT_SQL})'
    )

    op.execute('ALTER TABLE memory.memory_access_events ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE memory.memory_access_events FORCE ROW LEVEL SECURITY')
    op.execute(
        f'CREATE POLICY memory_access_events_owner_policy ON memory.memory_access_events '
        f'USING (owner_id = {OWNER_CONTEXT_SQL}) '
        f'WITH CHECK (owner_id = {OWNER_CONTEXT_SQL})'
    )


def downgrade() -> None:
    op.execute('DROP POLICY IF EXISTS memory_access_events_owner_policy ON memory.memory_access_events')
    op.execute('ALTER TABLE memory.memory_access_events NO FORCE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE memory.memory_access_events DISABLE ROW LEVEL SECURITY')

    op.execute('DROP POLICY IF EXISTS memories_owner_policy ON memory.memories')
    op.execute('ALTER TABLE memory.memories NO FORCE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE memory.memories DISABLE ROW LEVEL SECURITY')

    op.execute('ALTER DEFAULT PRIVILEGES IN SCHEMA memory REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM novo_runtime')
    op.execute('REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA memory FROM novo_runtime')
    op.execute('REVOKE USAGE ON SCHEMA memory FROM novo_runtime')

    op.drop_index('ix_memory_access_events_memory_created_at', table_name='memory_access_events', schema='memory')
    op.drop_index('ix_memory_access_events_owner_created_at', table_name='memory_access_events', schema='memory')
    op.drop_table('memory_access_events', schema='memory')

    op.drop_index('ix_memory_memories_source_type_source_id', table_name='memories', schema='memory')
    op.drop_index('ix_memory_memories_retention_until', table_name='memories', schema='memory')
    op.drop_index('ix_memory_memories_review_after', table_name='memories', schema='memory')
    op.drop_index('ix_memory_memories_owner_classification', table_name='memories', schema='memory')
    op.drop_index('ix_memory_memories_owner_status_kind', table_name='memories', schema='memory')
    op.drop_table('memories', schema='memory')
    op.execute('DROP SCHEMA IF EXISTS memory')
