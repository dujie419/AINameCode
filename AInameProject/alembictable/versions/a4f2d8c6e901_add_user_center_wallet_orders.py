"""add user center wallet orders

Revision ID: a4f2d8c6e901
Revises: 3f4a2c1d9b80
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4f2d8c6e901"
down_revision: Union[str, Sequence[str], None] = "3f4a2c1d9b80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("avatar", sa.String(length=500), nullable=True))
    op.add_column("user", sa.Column("nickname", sa.String(length=100), nullable=True))
    op.add_column("user", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("user", sa.Column("phone", sa.String(length=30), nullable=True))
    op.add_column("user", sa.Column("balance", sa.Numeric(12, 2), nullable=False, server_default="0.00"))
    op.add_column("user", sa.Column("is_expert", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.alter_column("experts", "price", existing_type=sa.Float(), type_=sa.Numeric(12, 2), existing_nullable=False)
    op.alter_column("expert_orders", "amount", existing_type=sa.Float(), type_=sa.Numeric(12, 2), existing_nullable=False)

    op.create_table(
        "recharge_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recharge_orders")),
    )
    op.create_index(op.f("ix_recharge_orders_user_id"), "recharge_orders", ["user_id"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_no", sa.String(length=64), nullable=False),
        sa.Column("order_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("related_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_orders")),
        sa.UniqueConstraint("order_no", name=op.f("uq_orders_order_no")),
    )
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)
    op.create_index(op.f("ix_orders_order_no"), "orders", ["order_no"], unique=False)
    op.create_index(op.f("ix_orders_order_type"), "orders", ["order_type"], unique=False)
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)

    op.create_table(
        "wallet_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("balance_after", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("related_order_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wallet_transactions")),
    )
    op.create_index(op.f("ix_wallet_transactions_user_id"), "wallet_transactions", ["user_id"], unique=False)
    op.create_index(op.f("ix_wallet_transactions_transaction_type"), "wallet_transactions", ["transaction_type"], unique=False)

    op.create_table(
        "expert_income_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("platform_fee", sa.Numeric(12, 2), nullable=False),
        sa.Column("actual_income", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expert_income_records")),
    )
    op.create_index(op.f("ix_expert_income_records_expert_id"), "expert_income_records", ["expert_id"], unique=False)
    op.create_index(op.f("ix_expert_income_records_user_id"), "expert_income_records", ["user_id"], unique=False)
    op.create_index(op.f("ix_expert_income_records_order_id"), "expert_income_records", ["order_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_expert_income_records_order_id"), table_name="expert_income_records")
    op.drop_index(op.f("ix_expert_income_records_user_id"), table_name="expert_income_records")
    op.drop_index(op.f("ix_expert_income_records_expert_id"), table_name="expert_income_records")
    op.drop_table("expert_income_records")
    op.drop_index(op.f("ix_wallet_transactions_transaction_type"), table_name="wallet_transactions")
    op.drop_index(op.f("ix_wallet_transactions_user_id"), table_name="wallet_transactions")
    op.drop_table("wallet_transactions")
    op.drop_index(op.f("ix_orders_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_order_type"), table_name="orders")
    op.drop_index(op.f("ix_orders_order_no"), table_name="orders")
    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_table("orders")
    op.drop_index(op.f("ix_recharge_orders_user_id"), table_name="recharge_orders")
    op.drop_table("recharge_orders")
    op.alter_column("expert_orders", "amount", existing_type=sa.Numeric(12, 2), type_=sa.Float(), existing_nullable=False)
    op.alter_column("experts", "price", existing_type=sa.Numeric(12, 2), type_=sa.Float(), existing_nullable=False)
    op.drop_column("user", "is_expert")
    op.drop_column("user", "balance")
    op.drop_column("user", "phone")
    op.drop_column("user", "bio")
    op.drop_column("user", "nickname")
    op.drop_column("user", "avatar")
