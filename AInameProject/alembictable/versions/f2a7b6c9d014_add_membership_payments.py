"""add membership payments

Revision ID: f2a7b6c9d014
Revises: e1f6a9b2c4d7
Create Date: 2026-06-23 00:00:00.000000

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a7b6c9d014"
down_revision: Union[str, Sequence[str], None] = "e1f6a9b2c4d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    now = datetime.now()
    op.create_table(
        "membership_plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_membership_plans")),
        sa.UniqueConstraint("code", name=op.f("uq_membership_plans_code")),
    )
    op.create_index(op.f("ix_membership_plans_code"), "membership_plans", ["code"], unique=True)
    op.create_index(op.f("ix_membership_plans_status"), "membership_plans", ["status"], unique=False)

    op.bulk_insert(
        sa.table(
            "membership_plans",
            sa.column("name", sa.String),
            sa.column("code", sa.String),
            sa.column("price", sa.Numeric),
            sa.column("duration_days", sa.Integer),
            sa.column("description", sa.String),
            sa.column("status", sa.String),
            sa.column("created_at", sa.DateTime),
        ),
        [
            {
                "name": "月度会员",
                "code": "monthly",
                "price": 29.90,
                "duration_days": 30,
                "description": "适合短期体验和轻量使用",
                "status": "active",
                "created_at": now,
            },
            {
                "name": "季度会员",
                "code": "quarterly",
                "price": 79.90,
                "duration_days": 90,
                "description": "适合持续起名和品牌方案迭代",
                "status": "active",
                "created_at": now,
            },
            {
                "name": "年度会员",
                "code": "yearly",
                "price": 199.00,
                "duration_days": 365,
                "description": "适合长期项目和高频使用",
                "status": "active",
                "created_at": now,
            },
        ],
    )

    op.create_table(
        "membership_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payment_order_id", sa.Integer(), nullable=True),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_membership_orders")),
    )
    op.create_index(op.f("ix_membership_orders_user_id"), "membership_orders", ["user_id"], unique=False)
    op.create_index(op.f("ix_membership_orders_plan_id"), "membership_orders", ["plan_id"], unique=False)
    op.create_index(op.f("ix_membership_orders_status"), "membership_orders", ["status"], unique=False)
    op.create_index(op.f("ix_membership_orders_payment_order_id"), "membership_orders", ["payment_order_id"], unique=False)

    op.create_table(
        "user_memberships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_memberships")),
    )
    op.create_index(op.f("ix_user_memberships_user_id"), "user_memberships", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_memberships_plan_id"), "user_memberships", ["plan_id"], unique=False)
    op.create_index(op.f("ix_user_memberships_status"), "user_memberships", ["status"], unique=False)
    op.create_index(op.f("ix_user_memberships_expires_at"), "user_memberships", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_memberships_expires_at"), table_name="user_memberships")
    op.drop_index(op.f("ix_user_memberships_status"), table_name="user_memberships")
    op.drop_index(op.f("ix_user_memberships_plan_id"), table_name="user_memberships")
    op.drop_index(op.f("ix_user_memberships_user_id"), table_name="user_memberships")
    op.drop_table("user_memberships")
    op.drop_index(op.f("ix_membership_orders_payment_order_id"), table_name="membership_orders")
    op.drop_index(op.f("ix_membership_orders_status"), table_name="membership_orders")
    op.drop_index(op.f("ix_membership_orders_plan_id"), table_name="membership_orders")
    op.drop_index(op.f("ix_membership_orders_user_id"), table_name="membership_orders")
    op.drop_table("membership_orders")
    op.drop_index(op.f("ix_membership_plans_status"), table_name="membership_plans")
    op.drop_index(op.f("ix_membership_plans_code"), table_name="membership_plans")
    op.drop_table("membership_plans")
