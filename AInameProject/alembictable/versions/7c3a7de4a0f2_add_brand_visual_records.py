"""add brand visual records

Revision ID: 7c3a7de4a0f2
Revises: 2b7c9f1a4d10
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c3a7de4a0f2"
down_revision: Union[str, Sequence[str], None] = "2b7c9f1a4d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brand_visual_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("industry", sa.String(length=100), nullable=False),
        sa.Column("style", sa.String(length=200), nullable=False),
        sa.Column("meaning", sa.Text(), nullable=False),
        sa.Column("slogan", sa.String(length=200), nullable=False),
        sa.Column("logo_prompt", sa.Text(), nullable=False),
        sa.Column("brand_report", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_brand_visual_records")),
    )
    op.create_index(op.f("ix_brand_visual_records_user_id"), "brand_visual_records", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_brand_visual_records_user_id"), table_name="brand_visual_records")
    op.drop_table("brand_visual_records")
