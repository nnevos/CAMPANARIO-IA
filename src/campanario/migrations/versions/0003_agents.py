"""persist active agent and response agent provenance

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("chat_sessions") as batch:
        batch.add_column(sa.Column("agent_id", sa.String(length=64), nullable=False, server_default="campanario"))
    with op.batch_alter_table("messages") as batch:
        batch.add_column(sa.Column("agent_id", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("messages") as batch:
        batch.drop_column("agent_id")
    with op.batch_alter_table("chat_sessions") as batch:
        batch.drop_column("agent_id")
