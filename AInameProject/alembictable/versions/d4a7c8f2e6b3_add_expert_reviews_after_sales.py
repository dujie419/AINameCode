"""add expert reviews and after sales

Revision ID: d4a7c8f2e6b3
Revises: c9e2f4a6b1d5
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4a7c8f2e6b3"
down_revision: Union[str, Sequence[str], None] = "c9e2f4a6b1d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expert_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("expert_order_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("reply", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("replied_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expert_reviews")),
        sa.UniqueConstraint("expert_order_id", "user_id", name="uq_expert_reviews_order_user"),
    )
    op.create_index(op.f("ix_expert_reviews_expert_id"), "expert_reviews", ["expert_id"], unique=False)
    op.create_index(op.f("ix_expert_reviews_expert_order_id"), "expert_reviews", ["expert_order_id"], unique=False)
    op.create_index(op.f("ix_expert_reviews_user_id"), "expert_reviews", ["user_id"], unique=False)
    op.create_index(op.f("ix_expert_reviews_status"), "expert_reviews", ["status"], unique=False)

    op.create_table(
        "after_sale_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("expert_order_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("request_no", sa.String(length=64), nullable=False),
        sa.Column("request_type", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("handled_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_after_sale_requests")),
        sa.UniqueConstraint("request_no", name=op.f("uq_after_sale_requests_request_no")),
    )
    op.create_index(op.f("ix_after_sale_requests_user_id"), "after_sale_requests", ["user_id"], unique=False)
    op.create_index(op.f("ix_after_sale_requests_expert_id"), "after_sale_requests", ["expert_id"], unique=False)
    op.create_index(op.f("ix_after_sale_requests_expert_order_id"), "after_sale_requests", ["expert_order_id"], unique=False)
    op.create_index(op.f("ix_after_sale_requests_order_id"), "after_sale_requests", ["order_id"], unique=False)
    op.create_index(op.f("ix_after_sale_requests_request_no"), "after_sale_requests", ["request_no"], unique=True)
    op.create_index(op.f("ix_after_sale_requests_request_type"), "after_sale_requests", ["request_type"], unique=False)
    op.create_index(op.f("ix_after_sale_requests_status"), "after_sale_requests", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_after_sale_requests_status"), table_name="after_sale_requests")
    op.drop_index(op.f("ix_after_sale_requests_request_type"), table_name="after_sale_requests")
    op.drop_index(op.f("ix_after_sale_requests_request_no"), table_name="after_sale_requests")
    op.drop_index(op.f("ix_after_sale_requests_order_id"), table_name="after_sale_requests")
    op.drop_index(op.f("ix_after_sale_requests_expert_order_id"), table_name="after_sale_requests")
    op.drop_index(op.f("ix_after_sale_requests_expert_id"), table_name="after_sale_requests")
    op.drop_index(op.f("ix_after_sale_requests_user_id"), table_name="after_sale_requests")
    op.drop_table("after_sale_requests")
    op.drop_index(op.f("ix_expert_reviews_status"), table_name="expert_reviews")
    op.drop_index(op.f("ix_expert_reviews_user_id"), table_name="expert_reviews")
    op.drop_index(op.f("ix_expert_reviews_expert_order_id"), table_name="expert_reviews")
    op.drop_index(op.f("ix_expert_reviews_expert_id"), table_name="expert_reviews")
    op.drop_table("expert_reviews")
