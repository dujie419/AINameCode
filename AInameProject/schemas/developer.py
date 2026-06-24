from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DeveloperApplyIn(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=200)
    contact_name: str = Field(..., min_length=2, max_length=100)


class DeveloperOut(BaseModel):
    id: int
    user_id: int
    company_name: str
    contact_name: str
    email: str
    status: str
    plan_id: int | None = None
    subscription_status: str | None = None
    subscription_expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ApiKeyCreateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    quota: int = Field(1000, ge=1)


class ApiKeyCreateOut(BaseModel):
    id: int
    name: str
    api_key: str
    secret_key: str
    quota: int


class ApiKeyOut(BaseModel):
    id: int
    name: str
    api_key_prefix: str
    secret_key_prefix: str
    status: str
    quota: int
    used_quota: int
    created_at: datetime | None = None


class DeveloperDashboardOut(BaseModel):
    api_key_count: int
    today_calls: int
    total_calls: int
    total_tokens: int
    month_cost: float
    plan_name: str | None = None
    plan_quota: int = 0
    plan_daily_quota: int = 0
    plan_qpm_limit: int = 60
    token_price: float = 0.0001
    subscription_status: str | None = None
    subscription_expires_at: datetime | None = None
    today_quota_used: int = 0
    month_quota_used: int = 0
    today_quota_remaining: int | None = None
    month_quota_remaining: int | None = None


class UsageLogOut(BaseModel):
    id: int
    endpoint: str
    tokens: int
    response_time: int
    request_ip: str | None = None
    status_code: int
    cost: float = 0
    created_at: datetime | None = None


class OpenApiCredential(BaseModel):
    developer_id: int
    api_key_id: int
    plan_id: int | None = None
    qpm_limit: int = 60
    daily_quota: int = 0
    monthly_quota: int = 0
    token_price: float = 0.0001


class OpenNameOut(BaseModel):
    name: str
    meaning: str | None = None
    tokens: int = 0


class NpcNameIn(BaseModel):
    race: str = Field(..., max_length=50)
    gender: str = Field(..., max_length=20)
    style: str = Field(..., max_length=100)


class NovelCharacterIn(BaseModel):
    novel_type: str = Field(..., max_length=100)
    gender: str = Field(..., max_length=20)


class LocationNameIn(BaseModel):
    style: str = Field(..., max_length=100)


class BabyNameIn(BaseModel):
    surname: str = Field(..., min_length=1, max_length=20)
    gender: str = Field(..., max_length=20)


class CompanyNameIn(BaseModel):
    industry: str = Field(..., max_length=100)
    style: str = Field(..., max_length=100)


class PageOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]


class PlanIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(0, ge=0)
    quota: int = Field(0, ge=0)
    daily_quota: int = Field(0, ge=0)
    qpm_limit: int = Field(60, ge=1)
    token_price: float = Field(0.0001, ge=0)
    billing_cycle: str = Field("month", pattern="^(month|year|once)$")
    description: str | None = None
    status: str = Field("active", pattern="^(active|disabled)$")


class PlanOut(PlanIn):
    id: int
    created_at: datetime | None = None


class SubscriptionCreateIn(BaseModel):
    plan_id: int
    months: int = Field(1, ge=1, le=36)


class DeveloperSubscriptionOut(BaseModel):
    id: int
    developer_id: int
    plan_id: int
    status: str
    started_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None


class RateLimitRuleIn(BaseModel):
    developer_id: int | None = None
    api_key_id: int | None = None
    endpoint: str = "*"
    qpm_limit: int = Field(60, ge=1)
    daily_quota: int = Field(0, ge=0)
    monthly_quota: int = Field(0, ge=0)
    status: str = Field("active", pattern="^(active|disabled)$")


class RateLimitRuleOut(RateLimitRuleIn):
    id: int
    created_at: datetime | None = None


class BillingSummaryOut(BaseModel):
    id: int
    developer_id: int
    period: str
    total_calls: int
    total_tokens: int
    total_cost: float
    status: str
    created_at: datetime | None = None
    closed_at: datetime | None = None


class ApiReconciliationOut(BaseModel):
    id: int
    period: str
    developer_id: int | None = None
    usage_log_count: int
    billing_record_count: int
    usage_tokens: int
    billed_tokens: int
    status: str
    created_at: datetime | None = None
