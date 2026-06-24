"""add admin system

Revision ID: 2b7c9f1a4d10
Revises: 8d819f48e26b
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2b7c9f1a4d10"
down_revision: Union[str, Sequence[str], None] = "8d819f48e26b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("status", sa.String(length=20), nullable=False, server_default="active"))
    op.add_column("user", sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.add_column("user", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))

    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_users")),
        sa.UniqueConstraint("username", name=op.f("uq_admin_users_username")),
    )
    op.create_index(op.f("ix_admin_users_username"), "admin_users", ["username"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_users_username"), table_name="admin_users")
    op.drop_table("admin_users")
    op.drop_column("user", "updated_at")
    op.drop_column("user", "created_at")
    op.drop_column("user", "status")
