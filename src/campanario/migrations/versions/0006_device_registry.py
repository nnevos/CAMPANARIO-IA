"""persist device registry identities and advertised capabilities

Revision ID: 0006
Revises: 0005
"""

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("connection_state", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_devices_connection_state", "devices", ["connection_state"])
    op.create_index("ix_devices_last_seen", "devices", ["last_seen"])


def downgrade() -> None:
    op.drop_index("ix_devices_last_seen", table_name="devices")
    op.drop_index("ix_devices_connection_state", table_name="devices")
    op.drop_table("devices")
