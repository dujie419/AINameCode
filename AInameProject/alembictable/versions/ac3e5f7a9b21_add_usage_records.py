"""add usage records

Revision ID: ac3e5f7a9b21
Revises: 9a2b4c6d8e10
Create Date: 2026-06-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "ac3e5f7a9b21"
down_revision = "9a2b4c6d8e10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usage_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("usage_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("remaining_quota", sa.Integer(), nullable=True),
        sa.Column("period_type", sa.String(length=20), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("related_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usage_records")),
    )
    op.create_index(op.f("ix_usage_records_user_id"), "usage_records", ["user_id"], unique=False)
    op.create_index(op.f("ix_usage_records_usage_type"), "usage_records", ["usage_type"], unique=False)
    op.create_index(op.f("ix_usage_records_period_type"), "usage_records", ["period_type"], unique=False)
    op.create_index(op.f("ix_usage_records_period_start"), "usage_records", ["period_start"], unique=False)
    op.create_index(op.f("ix_usage_records_related_id"), "usage_records", ["related_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_usage_records_related_id"), table_name="usage_records")
    op.drop_index(op.f("ix_usage_records_period_start"), table_name="usage_records")
    op.drop_index(op.f("ix_usage_records_period_type"), table_name="usage_records")
    op.drop_index(op.f("ix_usage_records_usage_type"), table_name="usage_records")
    op.drop_index(op.f("ix_usage_records_user_id"), table_name="usage_records")
    op.drop_table("usage_records")
