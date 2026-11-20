"""separate Campanario system identity from bridge agents

Revision ID: 0004
Revises: 0003
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Sessions that previously selected the mistaken pseudo-agent "campanario"
    # now use the real default bridge-agent, Morgana.
    op.execute(sa.text("UPDATE chat_sessions SET agent_id = 'morgana' WHERE agent_id = 'campanario' OR agent_id IS NULL"))
    # Historical assistant messages produced by the old neutral/system voice are
    # deliberately left unattributed rather than rewritten as if Morgana said them.
    op.execute(sa.text("UPDATE messages SET agent_id = NULL WHERE agent_id = 'campanario'"))
    with op.batch_alter_table("chat_sessions") as batch:
        batch.alter_column(
            "agent_id",
            existing_type=sa.String(length=64),
            nullable=False,
            server_default="morgana",
        )


def downgrade() -> None:
    with op.batch_alter_table("chat_sessions") as batch:
        batch.alter_column(
            "agent_id",
            existing_type=sa.String(length=64),
            nullable=False,
            server_default="campanario",
        )
