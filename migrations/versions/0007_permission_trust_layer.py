"""permission and trust layer

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table("devices") as batch:
        batch.add_column(sa.Column("trusted", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("credential_hash", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table("security_audit", sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("action", sa.String(64), nullable=False), sa.Column("principal_id", sa.String(128), nullable=False), sa.Column("device_id", sa.String(128), nullable=True), sa.Column("capability", sa.String(128), nullable=True), sa.Column("permission", sa.String(128), nullable=True), sa.Column("decision", sa.String(32), nullable=False), sa.Column("detail", sa.Text(), nullable=True))
    op.create_index("ix_security_audit_created_at", "security_audit", ["created_at"])

def downgrade() -> None:
    op.drop_index("ix_security_audit_created_at", table_name="security_audit")
    op.drop_table("security_audit")
    with op.batch_alter_table("devices") as batch:
        batch.drop_column("revoked_at"); batch.drop_column("credential_hash"); batch.drop_column("trusted")
