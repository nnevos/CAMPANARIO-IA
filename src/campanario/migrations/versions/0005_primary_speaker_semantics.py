"""rename session agent selection to primary-speaker priority

Revision ID: 0005
Revises: 0004
"""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("chat_sessions") as batch:
        batch.alter_column(
            "agent_id",
            new_column_name="primary_agent_id",
            existing_type=sa.String(length=64),
            nullable=False,
            server_default="morgana",
        )


def downgrade() -> None:
    with op.batch_alter_table("chat_sessions") as batch:
        batch.alter_column(
            "primary_agent_id",
            new_column_name="agent_id",
            existing_type=sa.String(length=64),
            nullable=False,
            server_default="morgana",
        )
