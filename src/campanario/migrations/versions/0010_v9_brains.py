"""Shared V9 brain registry and additive hero builds.

Revision ID: 0010
Revises: 0009
No chat, personality, memory or document rows are edited or dropped.
"""
from datetime import UTC, datetime
import json

from alembic import op
import sqlalchemy as sa

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('agent_builds',
        sa.Column('agent_id', sa.String(64), primary_key=True),
        sa.Column('revision', sa.Integer, nullable=False),
        sa.Column('config', sa.JSON, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('archetype_definitions',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('version', sa.String(24), nullable=False),
        sa.Column('description', sa.Text, nullable=False))
    op.create_table('talent_definitions',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('version', sa.String(24), nullable=False),
        sa.Column('definition', sa.JSON, nullable=False))
    op.create_table('agent_talents',
        sa.Column('agent_id', sa.String(64), sa.ForeignKey('agent_builds.agent_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('talent_id', sa.String(64), sa.ForeignKey('talent_definitions.id'), primary_key=True))
    op.create_table('brain_registry',
        sa.Column('brain_id', sa.String(64), primary_key=True),
        sa.Column('version', sa.String(32), nullable=False),
        sa.Column('state', sa.String(32), nullable=False))
    op.create_table('brain_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('request_id', sa.String(36), nullable=False),
        sa.Column('trace_id', sa.String(36), nullable=False),
        sa.Column('brain_id', sa.String(64), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('latency_ms', sa.Float, nullable=False),
        sa.Column('evidence_count', sa.Integer, nullable=False),
        sa.Column('operations', sa.JSON, nullable=False),
        sa.Column('error', sa.String(90), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_brain_runs_trace_id', 'brain_runs', ['trace_id'])
    op.create_index('ix_brain_runs_request_id', 'brain_runs', ['request_id'])
    # Conservative defaults preserve both personas with an empty / free build.
    from campanario.brains.builds import AgentBuild, ARCHETYPES, TALENTS
    conn = op.get_bind()
    for agent in ('morgana', 'todd'):
        build = AgentBuild(agent_id=agent)
        conn.execute(sa.text('INSERT INTO agent_builds(agent_id,revision,config,updated_at) VALUES (:a,:r,:c,:t)'),
                     {'a': agent, 'r': 1, 'c': json.dumps(build.model_dump(mode='json'), ensure_ascii=False),
                      't': datetime.now(UTC)})
    for archetype_id, description in ARCHETYPES.items():
        conn.execute(sa.text('INSERT INTO archetype_definitions(id,version,description) VALUES (:a,:v,:d)'),
                     {'a': archetype_id, 'v': '1.0', 'd': description})
    for talent in TALENTS.values():
        conn.execute(sa.text('INSERT INTO talent_definitions(id,version,definition) VALUES (:a,:v,:d)'),
                     {'a': talent.id, 'v': talent.version,
                      'd': json.dumps(talent.model_dump(mode='json'), ensure_ascii=False)})
    for brain in ('knowledge', 'analysis', 'investigation', 'programming', 'strategy', 'perception', 'communication', 'creation'):
        conn.execute(sa.text('INSERT INTO brain_registry(brain_id,version,state) VALUES (:a,:v,:s)'),
                     {'a': brain, 'v': '9.0', 's': 'ready' if brain in ('knowledge', 'analysis') else 'unavailable'})


def downgrade():
    # Only V9-specific tables are removed. Application rollback is safer by
    # setting the feature flag to false; this downgrade is for explicit use.
    op.drop_index('ix_brain_runs_request_id', table_name='brain_runs')
    op.drop_index('ix_brain_runs_trace_id', table_name='brain_runs')
    for name in ('brain_runs', 'agent_talents', 'brain_registry',
                 'talent_definitions', 'archetype_definitions', 'agent_builds'):
        op.drop_table(name)
