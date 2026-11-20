"""experience learning memory

Revision ID: 0009
Revises: 0008
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "experience_memories",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=128), nullable=False),
        sa.Column("key", sa.String(length=160), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("source_session_id", sa.String(length=36), nullable=True),
        sa.Column("source_message_id", sa.String(length=36), nullable=True),
        sa.Column("source_agent_id", sa.String(length=64), nullable=True),
        sa.Column("supersedes_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_recalled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recall_count", sa.Integer(), nullable=False, server_default="0"),
    )
    for column in ("kind", "subject", "key", "source", "status", "source_session_id", "source_message_id", "supersedes_id", "updated_at"):
        op.create_index(f"ix_experience_memories_{column}", "experience_memories", [column])


def downgrade() -> None:
    op.drop_table("experience_memories")
