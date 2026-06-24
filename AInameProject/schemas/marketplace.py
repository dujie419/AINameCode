from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class PageOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list


class ExpertApplyIn(BaseModel):
    name: Annotated[str, Field(..., min_length=1, max_length=100)]
    title: Annotated[str, Field(..., min_length=1, max_length=100)]
    description: str
    tags: list[str] = []
    avatar: str | None = None
    price: Annotated[Decimal, Field(gt=0, le=999999, max_digits=12, decimal_places=2)] = Decimal("99.00")
    experience_years: Annotated[int, Field(ge=0, le=80)] = 0


class ExpertOut(BaseModel):
    id: int
    user_id: int
    name: str
    avatar: str | None = None
    title: str
    description: str
    tags: list[str]
    price: float
    experience_years: int
    status: str
    rating: float
    created_at: datetime | None = None


class ExpertOrderCreateIn(BaseModel):
    expert_id: int
    name_record_id: int | None = None


class ExpertReportIn(BaseModel):
    summary: str
    analysis: str
    suggestions: str


class ExpertOrderOut(BaseModel):
    id: int
    order_id: int | None = None
    order_no: str | None = None
    user_id: int
    expert_id: int
    name_record_id: int | None = None
    amount: float
    fee_rate_snapshot: float | None = None
    platform_fee: float | None = None
    expert_income: float | None = None
    status: str
    report_url: str | None = None
    report_summary: str | None = None
    report_analysis: str | None = None
    report_suggestions: str | None = None
    delivered_at: datetime | None = None
    confirmed_at: datetime | None = None
    settlement_due_at: datetime | None = None
    settled_at: datetime | None = None
    created_at: datetime | None = None


class ExpertReviewCreateIn(BaseModel):
    rating: Annotated[int, Field(..., ge=1, le=5)]
    content: str = Field("", max_length=1000)


class ExpertReviewReplyIn(BaseModel):
    reply: str = Field(..., min_length=1, max_length=1000)


class ExpertReviewOut(BaseModel):
    id: int
    expert_id: int
    expert_order_id: int
    user_id: int
    rating: int
    content: str
    reply: str | None = None
    status: str
    created_at: datetime | None = None
    replied_at: datetime | None = None


class AfterSaleCreateIn(BaseModel):
    request_type: str = Field("refund", pattern="^(refund|redo|complaint)$")
    reason: str = Field("", max_length=255)
    description: str = Field("", max_length=2000)


class AfterSaleHandleIn(BaseModel):
    status: str = Field(..., pattern="^(processing|approved|rejected|closed)$")
    resolution: str = Field("", max_length=2000)


class AfterSaleOut(BaseModel):
    id: int
    user_id: int
    expert_id: int
    expert_order_id: int
    order_id: int | None = None
    request_no: str
    request_type: str
    reason: str
    description: str
    status: str
    resolution: str | None = None
    created_at: datetime | None = None
    handled_at: datetime | None = None


class CommunityPostCreateIn(BaseModel):
    title: Annotated[str, Field(..., min_length=1, max_length=200)]
    description: str = ""
    naming_type: Literal["人名", "企业名", "宠物名"] = "企业名"
    name_record_id: int | None = None
    candidates: list[str] = []


class CommunityCandidateOut(BaseModel):
    id: int
    post_id: int
    name_candidate_id: int | None = None
    name: str
    description: str = ""
    reference: str = ""
    moral: str = ""
    domain: str = ""
    vote_count: int


class CommunityPostOut(BaseModel):
    id: int
    user_id: int
    naming_type: str = "企业名"
    name_record_id: int | None = None
    title: str
    description: str
    status: str
    created_at: datetime | None = None
    candidates: list[CommunityCandidateOut] = []


class CommunityVoteIn(BaseModel):
    candidate_id: int


class CommunityResultOut(BaseModel):
    winner: str
    vote_count: int
