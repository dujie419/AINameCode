from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field


Money = Annotated[Decimal, Field(max_digits=12, decimal_places=2)]


class PageOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list


class UserProfileOut(BaseModel):
    id: int
    username: str
    email: str
    phone: str | None = None
    avatar: str | None = None
    nickname: str | None = None
    bio: str | None = None
    balance: Money
    frozen_balance: Money = Decimal("0.00")
    is_expert: bool
    membership_status: str = "inactive"
    membership_expires_at: datetime | None = None
    created_at: datetime | None = None


class UserProfileUpdateIn(BaseModel):
    nickname: str | None = None
    phone: str | None = None
    avatar: str | None = None
    bio: str | None = None


class BalanceOut(BaseModel):
    balance: Money


class RechargeCreateIn(BaseModel):
    amount: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
    provider: str = Field("virtual", max_length=50)


class RechargeOrderOut(BaseModel):
    recharge_order_id: int
    payment_order_id: int | None = None
    payment_no: str | None = None
    provider: str | None = None
    pay_url: str | None = None
    amount: Money
    status: str


class PaymentCallbackIn(BaseModel):
    payment_no: str
    provider_trade_no: str
    amount: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
    trade_status: str = "success"
    event_id: str
    signature: str | None = None
    raw_payload: dict = {}


class PaymentOrderOut(BaseModel):
    id: int
    user_id: int
    payment_no: str
    business_type: str
    business_id: int
    provider: str
    provider_trade_no: str | None = None
    amount: Money
    status: str
    pay_url: str | None = None
    created_at: datetime | None = None
    paid_at: datetime | None = None


class VirtualPayOut(BaseModel):
    payment: PaymentOrderOut
    message: str


class MembershipPlanOut(BaseModel):
    id: int
    name: str
    code: str
    price: Money
    duration_days: int
    description: str = ""
    status: str


class MembershipCreateIn(BaseModel):
    plan_id: int
    provider: str = Field("virtual", max_length=50)


class MembershipOrderOut(BaseModel):
    membership_order_id: int
    payment_order_id: int | None = None
    payment_no: str | None = None
    provider: str | None = None
    pay_url: str | None = None
    amount: Money
    status: str
    plan: MembershipPlanOut


class UserMembershipOut(BaseModel):
    status: str
    plan_id: int | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None


class UsageQuotaItemOut(BaseModel):
    usage_type: str
    label: str
    period_type: str
    quota: int
    used: int
    remaining: int
    bonus_remaining: int = 0
    period_start: date | None = None


class UsageQuotaSummaryOut(BaseModel):
    membership_status: str
    items: dict[str, UsageQuotaItemOut]


class RefundCreateIn(BaseModel):
    reason: str = Field("", max_length=255)


class RefundOrderOut(BaseModel):
    id: int
    user_id: int
    order_id: int | None = None
    payment_order_id: int | None = None
    refund_no: str
    provider: str
    amount: Money
    reason: str
    status: str
    created_at: datetime | None = None
    refunded_at: datetime | None = None


class InvoiceCreateIn(BaseModel):
    order_id: int | None = None
    title: str = Field(..., min_length=1, max_length=200)
    tax_no: str | None = Field(None, max_length=100)
    amount: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)] | None = None


class InvoiceOut(BaseModel):
    id: int
    user_id: int
    order_id: int | None = None
    invoice_no: str
    title: str
    tax_no: str | None = None
    amount: Money
    status: str
    file_url: str | None = None
    created_at: datetime | None = None
    issued_at: datetime | None = None


class OrderOut(BaseModel):
    id: int
    user_id: int
    order_no: str
    order_type: str
    amount: Money
    status: str
    related_id: int | None = None
    created_at: datetime | None = None
    paid_at: datetime | None = None
    completed_at: datetime | None = None


class WalletTransactionOut(BaseModel):
    id: int
    user_id: int
    transaction_type: str
    amount: Money
    balance_after: Money
    description: str
    related_order_id: int | None = None
    created_at: datetime | None = None


class ExpertCenterProfileOut(BaseModel):
    expert_id: int
    user_id: int
    name: str
    avatar: str | None = None
    title: str
    description: str
    tags: list[str]
    price: Money
    rating: float
    status: str
    total_orders: int
    completed_orders: int
    total_income: Money
    available_balance: Money
    frozen_balance: Money = Decimal("0.00")


class ExpertProfileUpdateIn(BaseModel):
    name: str | None = None
    avatar: str | None = None
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    price: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)] | None = None


class ExpertStatisticsOut(BaseModel):
    pending_orders: int
    completed_orders: int
    total_income: Money
    available_balance: Money
    frozen_balance: Money = Decimal("0.00")
    month_income: Money
    rating: float


class ExpertIncomeOut(BaseModel):
    id: int
    expert_id: int
    user_id: int
    order_id: int
    amount: Money
    platform_fee: Money
    actual_income: Money
    status: str
    settled_at: datetime | None = None
    reversed_at: datetime | None = None
    reverse_reason: str | None = None
    created_at: datetime | None = None


class ExpertWithdrawalCreateIn(BaseModel):
    amount: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
    account_name: str = Field(..., min_length=1, max_length=100)
    account_no: str = Field(..., min_length=1, max_length=100)
    bank_name: str = Field("", max_length=100)


class ExpertWithdrawalOut(BaseModel):
    id: int
    expert_id: int
    user_id: int
    withdrawal_no: str
    amount: Money
    account_name: str
    account_no: str
    bank_name: str
    status: str
    reason: str | None = None
    payment_channel: str | None = None
    payment_trade_no: str | None = None
    created_at: datetime | None = None
    reviewed_at: datetime | None = None
    paid_at: datetime | None = None
