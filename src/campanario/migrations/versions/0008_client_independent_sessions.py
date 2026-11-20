"""client independent session provenance

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("messages") as batch:
        batch.add_column(sa.Column("client_id", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("device_id", sa.String(length=128), nullable=True))
    op.create_index("ix_messages_client_id", "messages", ["client_id"])
    op.create_index("ix_messages_device_id", "messages", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_device_id", table_name="messages")
    op.drop_index("ix_messages_client_id", table_name="messages")
    with op.batch_alter_table("messages") as batch:
        batch.drop_column("device_id")
        batch.drop_column("client_id")
