"""add partner commissions

Revision ID: 6a1d8e4f9c20
Revises: 0f3e9d2c7b11
Create Date: 2026-06-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6a1d8e4f9c20"
down_revision: Union[str, Sequence[str], None] = "0f3e9d2c7b11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partner_commission_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("partner_user_id", sa.Integer(), nullable=False),
        sa.Column("buyer_user_id", sa.Integer(), nullable=False),
        sa.Column("attribution_id", sa.Integer(), nullable=False),
        sa.Column("business_type", sa.String(length=50), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("payment_order_id", sa.Integer(), nullable=True),
        sa.Column("base_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("commission_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("commission_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("settlement_due_at", sa.DateTime(), nullable=False),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
        sa.Column("reversed_at", sa.DateTime(), nullable=True),
        sa.Column("reverse_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_partner_commission_records")),
        sa.UniqueConstraint("business_type", "business_id", name="uq_partner_commissions_business"),
    )
    op.create_index(op.f("ix_partner_commission_records_partner_id"), "partner_commission_records", ["partner_id"], unique=False)
    op.create_index(op.f("ix_partner_commission_records_partner_user_id"), "partner_commission_records", ["partner_user_id"], unique=False)
    op.create_index(op.f("ix_partner_commission_records_buyer_user_id"), "partner_commission_records", ["buyer_user_id"], unique=False)
    op.create_index(op.f("ix_partner_commission_records_attribution_id"), "partner_commission_records", ["attribution_id"], unique=False)
    op.create_index(op.f("ix_partner_commission_records_business_type"), "partner_commission_records", ["business_type"], unique=False)
    op.create_index(op.f("ix_partner_commission_records_business_id"), "partner_commission_records", ["business_id"], unique=False)
    op.create_index(op.f("ix_partner_commission_records_order_id"), "partner_commission_records", ["order_id"], unique=False)
    op.create_index(op.f("ix_partner_commission_records_payment_order_id"), "partner_commission_records", ["payment_order_id"], unique=False)
    op.create_index(op.f("ix_partner_commission_records_status"), "partner_commission_records", ["status"], unique=False)
    op.create_index(op.f("ix_partner_commission_records_settlement_due_at"), "partner_commission_records", ["settlement_due_at"], unique=False)
    op.create_index(op.f("ix_partner_commission_records_created_at"), "partner_commission_records", ["created_at"], unique=False)

    op.create_table(
        "partner_withdrawals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("partner_user_id", sa.Integer(), nullable=False),
        sa.Column("withdrawal_no", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("account_name", sa.String(length=100), nullable=False),
        sa.Column("account_no", sa.String(length=100), nullable=False),
        sa.Column("bank_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("payment_channel", sa.String(length=50), nullable=True),
        sa.Column("payment_trade_no", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_partner_withdrawals")),
        sa.UniqueConstraint("withdrawal_no", name=op.f("uq_partner_withdrawals_withdrawal_no")),
    )
    op.create_index(op.f("ix_partner_withdrawals_partner_id"), "partner_withdrawals", ["partner_id"], unique=False)
    op.create_index(op.f("ix_partner_withdrawals_partner_user_id"), "partner_withdrawals", ["partner_user_id"], unique=False)
    op.create_index(op.f("ix_partner_withdrawals_withdrawal_no"), "partner_withdrawals", ["withdrawal_no"], unique=True)
    op.create_index(op.f("ix_partner_withdrawals_status"), "partner_withdrawals", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_partner_withdrawals_status"), table_name="partner_withdrawals")
    op.drop_index(op.f("ix_partner_withdrawals_withdrawal_no"), table_name="partner_withdrawals")
    op.drop_index(op.f("ix_partner_withdrawals_partner_user_id"), table_name="partner_withdrawals")
    op.drop_index(op.f("ix_partner_withdrawals_partner_id"), table_name="partner_withdrawals")
    op.drop_table("partner_withdrawals")

    op.drop_index(op.f("ix_partner_commission_records_created_at"), table_name="partner_commission_records")
    op.drop_index(op.f("ix_partner_commission_records_settlement_due_at"), table_name="partner_commission_records")
    op.drop_index(op.f("ix_partner_commission_records_status"), table_name="partner_commission_records")
    op.drop_index(op.f("ix_partner_commission_records_payment_order_id"), table_name="partner_commission_records")
    op.drop_index(op.f("ix_partner_commission_records_order_id"), table_name="partner_commission_records")
    op.drop_index(op.f("ix_partner_commission_records_business_id"), table_name="partner_commission_records")
    op.drop_index(op.f("ix_partner_commission_records_business_type"), table_name="partner_commission_records")
    op.drop_index(op.f("ix_partner_commission_records_attribution_id"), table_name="partner_commission_records")
    op.drop_index(op.f("ix_partner_commission_records_buyer_user_id"), table_name="partner_commission_records")
    op.drop_index(op.f("ix_partner_commission_records_partner_user_id"), table_name="partner_commission_records")
    op.drop_index(op.f("ix_partner_commission_records_partner_id"), table_name="partner_commission_records")
    op.drop_table("partner_commission_records")
