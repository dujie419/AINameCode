from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class PartnerApplyIn(BaseModel):
    partner_type: Literal["maternal_store", "business_agent"]
    name: Annotated[str, Field(..., min_length=1, max_length=100)]
    contact_phone: Annotated[str | None, Field(None, max_length=30)] = None
    company_name: Annotated[str | None, Field(None, max_length=200)] = None
    address: Annotated[str | None, Field(None, max_length=255)] = None
    description: Annotated[str, Field("", max_length=2000)] = ""


class PartnerOut(BaseModel):
    id: int
    user_id: int
    partner_type: str
    name: str
    contact_phone: str | None = None
    company_name: str | None = None
    address: str | None = None
    description: str = ""
    partner_code: str
    qr_payload: str = ""
    commission_rate: Decimal
    status: str
    reviewed_at: datetime | None = None
    review_reason: str | None = None
    created_at: datetime | None = None
    register_count: int = 0


class PartnerAttributionOut(BaseModel):
    id: int
    partner_id: int
    partner_user_id: int
    user_id: int
    partner_code: str
    source: str
    first_event: str
    created_at: datetime | None = None


class PartnerCommissionOut(BaseModel):
    id: int
    partner_id: int
    partner_user_id: int
    buyer_user_id: int
    business_type: str
    business_id: int
    order_id: int | None = None
    payment_order_id: int | None = None
    base_amount: Decimal
    commission_rate: Decimal
    commission_amount: Decimal
    status: str
    settlement_due_at: datetime | None = None
    settled_at: datetime | None = None
    reversed_at: datetime | None = None
    reverse_reason: str | None = None
    created_at: datetime | None = None


class PartnerWithdrawalCreateIn(BaseModel):
    amount: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
    account_name: Annotated[str, Field(..., min_length=1, max_length=100)]
    account_no: Annotated[str, Field(..., min_length=1, max_length=100)]
    bank_name: Annotated[str, Field("", max_length=100)] = ""


class PartnerWithdrawalOut(BaseModel):
    id: int
    partner_id: int
    partner_user_id: int
    withdrawal_no: str
    amount: Decimal
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


class PartnerFinanceSummaryOut(BaseModel):
    register_count: int = 0
    commission_total: Decimal = Decimal("0.00")
    pending_commission: Decimal = Decimal("0.00")
    settled_commission: Decimal = Decimal("0.00")
    reversed_commission: Decimal = Decimal("0.00")
    available_balance: Decimal = Decimal("0.00")
    frozen_balance: Decimal = Decimal("0.00")
