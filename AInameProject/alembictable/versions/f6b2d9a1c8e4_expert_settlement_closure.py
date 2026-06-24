"""expert settlement closure

Revision ID: f6b2d9a1c8e4
Revises: f2a7b6c9d014
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6b2d9a1c8e4"
down_revision: Union[str, Sequence[str], None] = "f2a7b6c9d014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("frozen_balance", sa.Numeric(12, 2), nullable=False, server_default="0.00"))

    op.create_table(
        "expert_fee_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("fee_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expert_fee_rules")),
    )
    op.create_index(op.f("ix_expert_fee_rules_status"), "expert_fee_rules", ["status"], unique=False)
    op.execute(
        "INSERT INTO expert_fee_rules (name, fee_rate, status, created_at) "
        "VALUES ('default expert service fee', 0.2000, 'active', CURRENT_TIMESTAMP)"
    )

    op.add_column("expert_orders", sa.Column("fee_rule_id", sa.Integer(), nullable=True))
    op.add_column("expert_orders", sa.Column("fee_rate_snapshot", sa.Numeric(5, 4), nullable=False, server_default="0.2000"))
    op.add_column("expert_orders", sa.Column("platform_fee", sa.Numeric(12, 2), nullable=False, server_default="0.00"))
    op.add_column("expert_orders", sa.Column("expert_income", sa.Numeric(12, 2), nullable=False, server_default="0.00"))
    op.add_column("expert_orders", sa.Column("delivered_at", sa.DateTime(), nullable=True))
    op.add_column("expert_orders", sa.Column("confirmed_at", sa.DateTime(), nullable=True))
    op.add_column("expert_orders", sa.Column("settlement_due_at", sa.DateTime(), nullable=True))
    op.add_column("expert_orders", sa.Column("settled_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_expert_orders_fee_rule_id"), "expert_orders", ["fee_rule_id"], unique=False)
    op.execute(
        "UPDATE expert_orders "
        "SET platform_fee = ROUND(amount * 0.2000, 2), "
        "expert_income = amount - ROUND(amount * 0.2000, 2) "
        "WHERE platform_fee = 0.00 AND expert_income = 0.00"
    )

    op.add_column("expert_income_records", sa.Column("settled_at", sa.DateTime(), nullable=True))
    op.add_column("expert_income_records", sa.Column("reversed_at", sa.DateTime(), nullable=True))
    op.add_column("expert_income_records", sa.Column("reverse_reason", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_expert_income_records_order_id", "expert_income_records", ["order_id"])

    op.create_table(
        "platform_ledgers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ledger_type", sa.String(length=30), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("expert_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_ledgers")),
    )
    op.create_index(op.f("ix_platform_ledgers_ledger_type"), "platform_ledgers", ["ledger_type"], unique=False)
    op.create_index(op.f("ix_platform_ledgers_order_id"), "platform_ledgers", ["order_id"], unique=False)
    op.create_index(op.f("ix_platform_ledgers_expert_id"), "platform_ledgers", ["expert_id"], unique=False)
    op.create_index(op.f("ix_platform_ledgers_user_id"), "platform_ledgers", ["user_id"], unique=False)

    op.add_column("expert_withdrawals", sa.Column("payment_channel", sa.String(length=50), nullable=True))
    op.add_column("expert_withdrawals", sa.Column("payment_trade_no", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("expert_withdrawals", "payment_trade_no")
    op.drop_column("expert_withdrawals", "payment_channel")
    op.drop_index(op.f("ix_platform_ledgers_user_id"), table_name="platform_ledgers")
    op.drop_index(op.f("ix_platform_ledgers_expert_id"), table_name="platform_ledgers")
    op.drop_index(op.f("ix_platform_ledgers_order_id"), table_name="platform_ledgers")
    op.drop_index(op.f("ix_platform_ledgers_ledger_type"), table_name="platform_ledgers")
    op.drop_table("platform_ledgers")
    op.drop_constraint("uq_expert_income_records_order_id", "expert_income_records", type_="unique")
    op.drop_column("expert_income_records", "reverse_reason")
    op.drop_column("expert_income_records", "reversed_at")
    op.drop_column("expert_income_records", "settled_at")
    op.drop_index(op.f("ix_expert_orders_fee_rule_id"), table_name="expert_orders")
    op.drop_column("expert_orders", "settled_at")
    op.drop_column("expert_orders", "settlement_due_at")
    op.drop_column("expert_orders", "confirmed_at")
    op.drop_column("expert_orders", "delivered_at")
    op.drop_column("expert_orders", "expert_income")
    op.drop_column("expert_orders", "platform_fee")
    op.drop_column("expert_orders", "fee_rate_snapshot")
    op.drop_column("expert_orders", "fee_rule_id")
    op.drop_index(op.f("ix_expert_fee_rules_status"), table_name="expert_fee_rules")
    op.drop_table("expert_fee_rules")
    op.drop_column("user", "frozen_balance")
