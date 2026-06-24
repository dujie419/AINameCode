"""add marketplace

Revision ID: 9e11fd12b7aa
Revises: 7c3a7de4a0f2
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9e11fd12b7aa"
down_revision: Union[str, Sequence[str], None] = "7c3a7de4a0f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("experts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("avatar", sa.String(length=500), nullable=True),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tags", sa.String(length=500), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("experience_years", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experts")))
    op.create_index(op.f("ix_experts_user_id"), "experts", ["user_id"], unique=False)
    op.create_table("expert_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("name_record_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("report_url", sa.String(length=500), nullable=True),
        sa.Column("report_summary", sa.Text(), nullable=True),
        sa.Column("report_analysis", sa.Text(), nullable=True),
        sa.Column("report_suggestions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expert_orders")))
    op.create_index(op.f("ix_expert_orders_user_id"), "expert_orders", ["user_id"], unique=False)
    op.create_index(op.f("ix_expert_orders_expert_id"), "expert_orders", ["expert_id"], unique=False)
    op.create_table("community_posts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_community_posts")))
    op.create_index(op.f("ix_community_posts_user_id"), "community_posts", ["user_id"], unique=False)
    op.create_table("community_candidates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("vote_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_community_candidates")))
    op.create_index(op.f("ix_community_candidates_post_id"), "community_candidates", ["post_id"], unique=False)
    op.create_table("community_votes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_community_votes")),
        sa.UniqueConstraint("post_id", "user_id", name="uq_community_votes_post_user"))
    op.create_index(op.f("ix_community_votes_post_id"), "community_votes", ["post_id"], unique=False)
    op.create_index(op.f("ix_community_votes_candidate_id"), "community_votes", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_community_votes_user_id"), "community_votes", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("community_votes")
    op.drop_table("community_candidates")
    op.drop_table("community_posts")
    op.drop_table("expert_orders")
    op.drop_table("experts")
