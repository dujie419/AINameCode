from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class RechargeOrder(Base):
    __tablename__ = "recharge_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    payment_method: Mapped[str] = mapped_column(String(50), default="mock")
    payment_order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class MembershipPlan(Base):
    __tablename__ = "membership_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    duration_days: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class MembershipOrder(Base):
    __tablename__ = "membership_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    plan_id: Mapped[int] = mapped_column(Integer, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    payment_order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class UserMembership(Base):
    __tablename__ = "user_memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    plan_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    order_type: Mapped[str] = mapped_column(String(50), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    related_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    transaction_type: Mapped[str] = mapped_column(String(30), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str] = mapped_column(String(255), default="")
    related_order_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    usage_type: Mapped[str] = mapped_column(String(50), index=True)
    amount: Mapped[int] = mapped_column(Integer, default=1)
    remaining_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    period_type: Mapped[str] = mapped_column(String(20), default="monthly", index=True)
    period_start: Mapped[date] = mapped_column(Date, index=True)
    reason: Mapped[str] = mapped_column(String(255), default="")
    related_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ExpertIncomeRecord(Base):
    __tablename__ = "expert_income_records"
    __table_args__ = (UniqueConstraint("order_id", name="uq_expert_income_records_order_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expert_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    order_id: Mapped[int] = mapped_column(Integer, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    platform_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    actual_income: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="settle_pending")
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reverse_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ExpertFeeRule(Base):
    __tablename__ = "expert_fee_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    fee_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.2000"))
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PlatformLedger(Base):
    __tablename__ = "platform_ledgers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ledger_type: Mapped[str] = mapped_column(String(30), index=True)
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    expert_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    payment_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    business_type: Mapped[str] = mapped_column(String(50), index=True)
    business_id: Mapped[int] = mapped_column(Integer, index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    provider_trade_no: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    pay_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_request: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_order_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    transaction_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    provider_trade_no: Mapped[str] = mapped_column(String(128), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), index=True)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PaymentCallbackEvent(Base):
    __tablename__ = "payment_callback_events"
    __table_args__ = (UniqueConstraint("provider", "event_id", name="uq_payment_callback_events_provider_event"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    event_id: Mapped[str] = mapped_column(String(128), index=True)
    payment_no: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(20), default="processed")
    raw_payload: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class RefundOrder(Base):
    __tablename__ = "refund_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    payment_order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    refund_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    provider_refund_no: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    reason: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ReconciliationRecord(Base):
    __tablename__ = "reconciliation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    reconcile_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    matched_count: Mapped[int] = mapped_column(Integer, default=0)
    mismatch_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    report_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    invoice_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    tax_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ExpertWithdrawal(Base):
    __tablename__ = "expert_withdrawals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expert_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    withdrawal_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    account_name: Mapped[str] = mapped_column(String(100))
    account_no: Mapped[str] = mapped_column(String(100))
    bank_name: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_trade_no: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
