"""add payment tables

Revision ID: c9e2f4a6b1d5
Revises: b8f1d2c3a9e0
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9e2f4a6b1d5"
down_revision: Union[str, Sequence[str], None] = "b8f1d2c3a9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recharge_orders", sa.Column("payment_order_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_recharge_orders_payment_order_id"), "recharge_orders", ["payment_order_id"], unique=False)

    op.create_table(
        "payment_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("payment_no", sa.String(length=64), nullable=False),
        sa.Column("business_type", sa.String(length=50), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_trade_no", sa.String(length=128), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("pay_url", sa.String(length=500), nullable=True),
        sa.Column("raw_request", sa.Text(), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_orders")),
        sa.UniqueConstraint("payment_no", name=op.f("uq_payment_orders_payment_no")),
    )
    op.create_index(op.f("ix_payment_orders_user_id"), "payment_orders", ["user_id"], unique=False)
    op.create_index(op.f("ix_payment_orders_payment_no"), "payment_orders", ["payment_no"], unique=True)
    op.create_index(op.f("ix_payment_orders_business_type"), "payment_orders", ["business_type"], unique=False)
    op.create_index(op.f("ix_payment_orders_business_id"), "payment_orders", ["business_id"], unique=False)
    op.create_index(op.f("ix_payment_orders_provider"), "payment_orders", ["provider"], unique=False)
    op.create_index(op.f("ix_payment_orders_provider_trade_no"), "payment_orders", ["provider_trade_no"], unique=False)
    op.create_index(op.f("ix_payment_orders_status"), "payment_orders", ["status"], unique=False)

    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("payment_order_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("transaction_no", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_trade_no", sa.String(length=128), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("raw_payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_transactions")),
        sa.UniqueConstraint("transaction_no", name=op.f("uq_payment_transactions_transaction_no")),
    )
    op.create_index(op.f("ix_payment_transactions_payment_order_id"), "payment_transactions", ["payment_order_id"], unique=False)
    op.create_index(op.f("ix_payment_transactions_user_id"), "payment_transactions", ["user_id"], unique=False)
    op.create_index(op.f("ix_payment_transactions_transaction_no"), "payment_transactions", ["transaction_no"], unique=True)
    op.create_index(op.f("ix_payment_transactions_provider"), "payment_transactions", ["provider"], unique=False)
    op.create_index(op.f("ix_payment_transactions_provider_trade_no"), "payment_transactions", ["provider_trade_no"], unique=False)
    op.create_index(op.f("ix_payment_transactions_status"), "payment_transactions", ["status"], unique=False)

    op.create_table(
        "payment_callback_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("payment_no", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_callback_events")),
        sa.UniqueConstraint("provider", "event_id", name="uq_payment_callback_events_provider_event"),
    )
    op.create_index(op.f("ix_payment_callback_events_provider"), "payment_callback_events", ["provider"], unique=False)
    op.create_index(op.f("ix_payment_callback_events_event_id"), "payment_callback_events", ["event_id"], unique=False)
    op.create_index(op.f("ix_payment_callback_events_payment_no"), "payment_callback_events", ["payment_no"], unique=False)

    op.create_table(
        "refund_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("payment_order_id", sa.Integer(), nullable=True),
        sa.Column("refund_no", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_refund_no", sa.String(length=128), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("refunded_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refund_orders")),
        sa.UniqueConstraint("refund_no", name=op.f("uq_refund_orders_refund_no")),
    )
    op.create_index(op.f("ix_refund_orders_user_id"), "refund_orders", ["user_id"], unique=False)
    op.create_index(op.f("ix_refund_orders_order_id"), "refund_orders", ["order_id"], unique=False)
    op.create_index(op.f("ix_refund_orders_payment_order_id"), "refund_orders", ["payment_order_id"], unique=False)
    op.create_index(op.f("ix_refund_orders_refund_no"), "refund_orders", ["refund_no"], unique=True)
    op.create_index(op.f("ix_refund_orders_provider"), "refund_orders", ["provider"], unique=False)
    op.create_index(op.f("ix_refund_orders_provider_refund_no"), "refund_orders", ["provider_refund_no"], unique=False)
    op.create_index(op.f("ix_refund_orders_status"), "refund_orders", ["status"], unique=False)

    op.create_table(
        "reconciliation_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("reconcile_date", sa.DateTime(), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("matched_count", sa.Integer(), nullable=False),
        sa.Column("mismatch_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("report_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reconciliation_records")),
    )
    op.create_index(op.f("ix_reconciliation_records_provider"), "reconciliation_records", ["provider"], unique=False)
    op.create_index(op.f("ix_reconciliation_records_reconcile_date"), "reconciliation_records", ["reconcile_date"], unique=False)
    op.create_index(op.f("ix_reconciliation_records_status"), "reconciliation_records", ["status"], unique=False)

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("invoice_no", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("tax_no", sa.String(length=100), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invoices")),
        sa.UniqueConstraint("invoice_no", name=op.f("uq_invoices_invoice_no")),
    )
    op.create_index(op.f("ix_invoices_user_id"), "invoices", ["user_id"], unique=False)
    op.create_index(op.f("ix_invoices_order_id"), "invoices", ["order_id"], unique=False)
    op.create_index(op.f("ix_invoices_invoice_no"), "invoices", ["invoice_no"], unique=True)
    op.create_index(op.f("ix_invoices_status"), "invoices", ["status"], unique=False)

    op.create_table(
        "expert_withdrawals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("withdrawal_no", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("account_name", sa.String(length=100), nullable=False),
        sa.Column("account_no", sa.String(length=100), nullable=False),
        sa.Column("bank_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expert_withdrawals")),
        sa.UniqueConstraint("withdrawal_no", name=op.f("uq_expert_withdrawals_withdrawal_no")),
    )
    op.create_index(op.f("ix_expert_withdrawals_expert_id"), "expert_withdrawals", ["expert_id"], unique=False)
    op.create_index(op.f("ix_expert_withdrawals_user_id"), "expert_withdrawals", ["user_id"], unique=False)
    op.create_index(op.f("ix_expert_withdrawals_withdrawal_no"), "expert_withdrawals", ["withdrawal_no"], unique=True)
    op.create_index(op.f("ix_expert_withdrawals_status"), "expert_withdrawals", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_expert_withdrawals_status"), table_name="expert_withdrawals")
    op.drop_index(op.f("ix_expert_withdrawals_withdrawal_no"), table_name="expert_withdrawals")
    op.drop_index(op.f("ix_expert_withdrawals_user_id"), table_name="expert_withdrawals")
    op.drop_index(op.f("ix_expert_withdrawals_expert_id"), table_name="expert_withdrawals")
    op.drop_table("expert_withdrawals")
    op.drop_index(op.f("ix_invoices_status"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_invoice_no"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_order_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_user_id"), table_name="invoices")
    op.drop_table("invoices")
    op.drop_index(op.f("ix_reconciliation_records_status"), table_name="reconciliation_records")
    op.drop_index(op.f("ix_reconciliation_records_reconcile_date"), table_name="reconciliation_records")
    op.drop_index(op.f("ix_reconciliation_records_provider"), table_name="reconciliation_records")
    op.drop_table("reconciliation_records")
    op.drop_index(op.f("ix_refund_orders_status"), table_name="refund_orders")
    op.drop_index(op.f("ix_refund_orders_provider_refund_no"), table_name="refund_orders")
    op.drop_index(op.f("ix_refund_orders_provider"), table_name="refund_orders")
    op.drop_index(op.f("ix_refund_orders_refund_no"), table_name="refund_orders")
    op.drop_index(op.f("ix_refund_orders_payment_order_id"), table_name="refund_orders")
    op.drop_index(op.f("ix_refund_orders_order_id"), table_name="refund_orders")
    op.drop_index(op.f("ix_refund_orders_user_id"), table_name="refund_orders")
    op.drop_table("refund_orders")
    op.drop_index(op.f("ix_payment_callback_events_payment_no"), table_name="payment_callback_events")
    op.drop_index(op.f("ix_payment_callback_events_event_id"), table_name="payment_callback_events")
    op.drop_index(op.f("ix_payment_callback_events_provider"), table_name="payment_callback_events")
    op.drop_table("payment_callback_events")
    op.drop_index(op.f("ix_payment_transactions_status"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_provider_trade_no"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_provider"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_transaction_no"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_user_id"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_payment_order_id"), table_name="payment_transactions")
    op.drop_table("payment_transactions")
    op.drop_index(op.f("ix_payment_orders_status"), table_name="payment_orders")
    op.drop_index(op.f("ix_payment_orders_provider_trade_no"), table_name="payment_orders")
    op.drop_index(op.f("ix_payment_orders_provider"), table_name="payment_orders")
    op.drop_index(op.f("ix_payment_orders_business_id"), table_name="payment_orders")
    op.drop_index(op.f("ix_payment_orders_business_type"), table_name="payment_orders")
    op.drop_index(op.f("ix_payment_orders_payment_no"), table_name="payment_orders")
    op.drop_index(op.f("ix_payment_orders_user_id"), table_name="payment_orders")
    op.drop_table("payment_orders")
    op.drop_index(op.f("ix_recharge_orders_payment_order_id"), table_name="recharge_orders")
    op.drop_column("recharge_orders", "payment_order_id")
