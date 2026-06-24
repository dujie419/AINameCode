from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, Field


AdminUsernameStr = Annotated[str, Field(..., min_length=4, max_length=50)]
AdminPasswordStr = Annotated[str, Field(..., min_length=6, max_length=50)]


class AdminLoginIn(BaseModel):
    username: AdminUsernameStr
    password: AdminPasswordStr


class AdminLoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class AdminTokenData(BaseModel):
    admin_id: int
    username: str
    role: str
    status: str


class AdminUserOut(BaseModel):
    id: int
    username: str
    role: str
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserAdminOut(BaseModel):
    id: int
    username: str
    email: str
    status: str = "active"
    user_level: str = "normal"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserStatusIn(BaseModel):
    status: Annotated[str, Field(..., pattern="^(active|disabled)$")]


class AdminAuditOut(BaseModel):
    id: int
    admin_id: int
    user_id: int
    action_type: str
    target_field: str
    before_value: str
    after_value: str
    reason: str
    created_at: datetime | None = None


class AdminQuotaItemOut(BaseModel):
    usage_type: str
    label: str
    period_type: str
    quota: int
    used: int
    remaining: int
    period_start: Any = None


class UserAdminDetailOut(UserAdminOut):
    balance: Decimal = Decimal("0.00")
    frozen_balance: Decimal = Decimal("0.00")
    membership_status: str = "inactive"
    membership_expires_at: datetime | None = None
    quota_items: dict[str, AdminQuotaItemOut] = Field(default_factory=dict)
    usage_totals: dict[str, int] = Field(default_factory=dict)
    audit_logs: list[AdminAuditOut] = Field(default_factory=list)


class AdminReasonIn(BaseModel):
    reason: Annotated[str, Field(..., min_length=1, max_length=255)]


class BalanceAdjustIn(AdminReasonIn):
    amount: Annotated[Decimal, Field(..., max_digits=12, decimal_places=2)]


class QuotaAdjustIn(AdminReasonIn):
    usage_type: Annotated[str, Field(..., pattern="^(name_generate|business_card|image_generate|vote_publish)$")]
    amount: int


class MembershipAdjustIn(AdminReasonIn):
    action: Annotated[str, Field(..., pattern="^(open|extend|cancel)$")]
    days: int = Field(30, ge=1, le=3650)


class UserLevelIn(AdminReasonIn):
    user_level: Annotated[str, Field(..., min_length=1, max_length=30)]


class PageOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]


class NameRecordQueryOut(BaseModel):
    id: int | None = None
    user_id: int | None = None
    naming_type: str | None = None
    keyword: str | None = None
    content: dict | None = None
    created_at: datetime | None = None


class DashboardStatisticsOut(BaseModel):
    user_total: int
    today_new_users: int
    name_record_total: int
    today_name_count: int
    admin_total: int
    expert_total: int = 0
    pending_expert_total: int = 0
    expert_order_total: int = 0
    community_post_total: int = 0
    community_vote_total: int = 0
    hot_names_top10: list[dict] = []
