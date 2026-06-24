"""add brand visual mode

Revision ID: 9a2b4c6d8e10
Revises: f6b2d9a1c8e4
Create Date: 2026-06-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "9a2b4c6d8e10"
down_revision = "f6b2d9a1c8e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("brand_visual_records", sa.Column("mode", sa.String(length=20), nullable=False, server_default="brand"))
    op.create_index(op.f("ix_brand_visual_records_mode"), "brand_visual_records", ["mode"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_brand_visual_records_mode"), table_name="brand_visual_records")
    op.drop_column("brand_visual_records", "mode")
