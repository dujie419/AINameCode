"""add admin user operations

Revision ID: cf7a1b3d5e92
Revises: bd4f6a8c2e90
Create Date: 2026-06-24 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cf7a1b3d5e92"
down_revision: Union[str, Sequence[str], None] = "bd4f6a8c2e90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("user_level", sa.String(length=30), nullable=False, server_default="normal"))
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("target_field", sa.String(length=50), nullable=False),
        sa.Column("before_value", sa.Text(), nullable=False),
        sa.Column("after_value", sa.Text(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_audit_logs")),
    )
    op.create_index(op.f("ix_admin_audit_logs_admin_id"), "admin_audit_logs", ["admin_id"], unique=False)
    op.create_index(op.f("ix_admin_audit_logs_user_id"), "admin_audit_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_admin_audit_logs_action_type"), "admin_audit_logs", ["action_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_audit_logs_action_type"), table_name="admin_audit_logs")
    op.drop_index(op.f("ix_admin_audit_logs_user_id"), table_name="admin_audit_logs")
    op.drop_index(op.f("ix_admin_audit_logs_admin_id"), table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")
    op.drop_column("user", "user_level")
