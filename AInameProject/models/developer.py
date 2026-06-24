from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Developer(Base):
    __tablename__ = "developers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, unique=True)
    company_name: Mapped[str] = mapped_column(String(200))
    contact_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    plan_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    subscription_status: Mapped[str] = mapped_column(String(20), default="inactive", index=True)
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    developer_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(100))
    api_key_prefix: Mapped[str] = mapped_column(String(20), index=True)
    api_key_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    secret_key_prefix: Mapped[str] = mapped_column(String(20))
    secret_key_encrypted: Mapped[str] = mapped_column(Text)
    secret_key_hash: Mapped[str] = mapped_column(String(128), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    quota: Mapped[int] = mapped_column(Integer, default=1000)
    used_quota: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ApiUsageLog(Base):
    __tablename__ = "api_usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    developer_id: Mapped[int] = mapped_column(Integer, index=True)
    api_key_id: Mapped[int] = mapped_column(Integer, index=True)
    endpoint: Mapped[str] = mapped_column(String(100), index=True)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    request_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    response_time: Mapped[int] = mapped_column(Integer, default=0)
    request_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class BillingRecord(Base):
    __tablename__ = "billing_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    developer_id: Mapped[int] = mapped_column(Integer, index=True)
    api_key_id: Mapped[int] = mapped_column(Integer, index=True)
    usage_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    price: Mapped[float] = mapped_column(Float, default=0)
    quota: Mapped[int] = mapped_column(Integer, default=0)
    daily_quota: Mapped[int] = mapped_column(Integer, default=0)
    qpm_limit: Mapped[int] = mapped_column(Integer, default=60)
    token_price: Mapped[float] = mapped_column(Float, default=0.0001)
    billing_cycle: Mapped[str] = mapped_column(String(20), default="month")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class DeveloperSubscription(Base):
    __tablename__ = "developer_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    developer_id: Mapped[int] = mapped_column(Integer, index=True)
    plan_id: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ApiRateLimitRule(Base):
    __tablename__ = "api_rate_limit_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    developer_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    api_key_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    endpoint: Mapped[str] = mapped_column(String(100), default="*", index=True)
    qpm_limit: Mapped[int] = mapped_column(Integer, default=60)
    daily_quota: Mapped[int] = mapped_column(Integer, default=0)
    monthly_quota: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ApiBillingSummary(Base):
    __tablename__ = "api_billing_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    developer_id: Mapped[int] = mapped_column(Integer, index=True)
    period: Mapped[str] = mapped_column(String(20), index=True)
    total_calls: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ApiReconciliationRecord(Base):
    __tablename__ = "api_reconciliation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(String(20), index=True)
    developer_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    usage_log_count: Mapped[int] = mapped_column(Integer, default=0)
    billing_record_count: Mapped[int] = mapped_column(Integer, default=0)
    usage_tokens: Mapped[int] = mapped_column(Integer, default=0)
    billed_tokens: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="matched", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
