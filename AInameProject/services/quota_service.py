from dataclasses import dataclass
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.account import UsageRecord, UserMembership
from models.growth import UserQuotaGrant


FREE_LIMITS = {
    "name_generate": {"period_type": "daily", "quota": 1},
    "business_card": {"period_type": "monthly", "quota": 0},
    "image_generate": {"period_type": "monthly", "quota": 0},
    "vote_publish": {"period_type": "monthly", "quota": 0},
}

VIP_LIMITS = {
    "name_generate": {"period_type": "monthly", "quota": 30},
    "business_card": {"period_type": "monthly", "quota": 5},
    "image_generate": {"period_type": "monthly", "quota": 5},
    "vote_publish": {"period_type": "monthly", "quota": 5},
}

USAGE_LABELS = {
    "name_generate": "起名次数",
    "business_card": "名片方案次数",
    "image_generate": "图片生成次数",
    "vote_publish": "投票发布次数",
}


@dataclass
class QuotaState:
    usage_type: str
    period_type: str
    quota: int
    used: int
    remaining: int
    membership_status: str
    period_start: date
    bonus_remaining: int = 0


def current_period_start(period_type: str) -> date:
    today = date.today()
    if period_type == "daily":
        return today
    return today.replace(day=1)


async def get_active_membership(user_id: int, session: AsyncSession) -> UserMembership | None:
    now = datetime.now()
    return await session.scalar(
        select(UserMembership)
        .where(
            UserMembership.user_id == int(user_id),
            UserMembership.status == "active",
            UserMembership.expires_at > now,
        )
        .order_by(UserMembership.expires_at.desc())
    )


async def is_vip_user(user_id: int, session: AsyncSession) -> bool:
    return bool(await get_active_membership(user_id, session))


def limits_for_membership(is_vip: bool) -> dict:
    return VIP_LIMITS if is_vip else FREE_LIMITS


async def get_usage_state(user_id: int, usage_type: str, session: AsyncSession) -> QuotaState:
    is_vip = await is_vip_user(user_id, session)
    membership_status = "vip" if is_vip else "free"
    config = limits_for_membership(is_vip).get(usage_type)
    if not config:
        raise HTTPException(status_code=400, detail="未知额度类型")

    period_type = config["period_type"]
    quota = int(config["quota"])
    period_start = current_period_start(period_type)
    used = await session.scalar(
        select(func.coalesce(func.sum(UsageRecord.amount), 0)).where(
            UsageRecord.user_id == int(user_id),
            UsageRecord.usage_type == usage_type,
            UsageRecord.period_type == period_type,
            UsageRecord.period_start == period_start,
        )
    ) or 0
    base_remaining = max(quota - int(used), 0)
    bonus_remaining = await session.scalar(
        select(func.coalesce(func.sum(UserQuotaGrant.total_amount - UserQuotaGrant.used_amount), 0)).where(
            UserQuotaGrant.user_id == int(user_id),
            UserQuotaGrant.usage_type == usage_type,
            UserQuotaGrant.status == "active",
            UserQuotaGrant.total_amount > UserQuotaGrant.used_amount,
            ((UserQuotaGrant.expires_at.is_(None)) | (UserQuotaGrant.expires_at > datetime.now())),
        )
    ) or 0
    remaining = base_remaining + int(bonus_remaining)
    return QuotaState(
        usage_type=usage_type,
        period_type=period_type,
        quota=quota,
        used=int(used),
        remaining=remaining,
        membership_status=membership_status,
        period_start=period_start,
        bonus_remaining=int(bonus_remaining),
    )


async def ensure_quota_available(user_id: int, usage_type: str, session: AsyncSession, amount: int = 1) -> QuotaState:
    state = await get_usage_state(user_id, usage_type, session)
    if state.remaining < amount:
        label = USAGE_LABELS.get(usage_type, "额度")
        raise HTTPException(
            status_code=402,
            detail=f"{label}不足，当前剩余 {state.remaining} 次，请开通 VIP 或购买额外次数包",
        )
    return state


async def record_usage(
        user_id: int,
        usage_type: str,
        session: AsyncSession,
        amount: int = 1,
        reason: str = "",
        related_id: int | None = None,
) -> UsageRecord:
    state = await get_usage_state(user_id, usage_type, session)
    base_remaining = max(state.quota - state.used, 0)
    bonus_to_consume = max(amount - base_remaining, 0)
    if bonus_to_consume > 0:
        grant_result = await session.execute(
            select(UserQuotaGrant)
            .where(
                UserQuotaGrant.user_id == int(user_id),
                UserQuotaGrant.usage_type == usage_type,
                UserQuotaGrant.status == "active",
                UserQuotaGrant.total_amount > UserQuotaGrant.used_amount,
                ((UserQuotaGrant.expires_at.is_(None)) | (UserQuotaGrant.expires_at > datetime.now())),
            )
            .order_by(UserQuotaGrant.expires_at.asc(), UserQuotaGrant.id.asc())
        )
        remaining_bonus_to_consume = bonus_to_consume
        for grant in grant_result.scalars().all():
            available = max(int(grant.total_amount) - int(grant.used_amount), 0)
            if available <= 0:
                continue
            used_from_grant = min(available, remaining_bonus_to_consume)
            grant.used_amount = int(grant.used_amount) + used_from_grant
            if grant.used_amount >= grant.total_amount:
                grant.status = "used"
            remaining_bonus_to_consume -= used_from_grant
            if remaining_bonus_to_consume <= 0:
                break
    remaining = max(state.remaining - amount, 0)
    record = UsageRecord(
        user_id=int(user_id),
        usage_type=usage_type,
        amount=amount,
        remaining_quota=remaining,
        period_type=state.period_type,
        period_start=state.period_start,
        reason=reason or USAGE_LABELS.get(usage_type, usage_type),
        related_id=related_id,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def quota_summary(user_id: int, session: AsyncSession) -> dict:
    is_vip = await is_vip_user(user_id, session)
    items = {}
    for usage_type in ("name_generate", "business_card", "image_generate", "vote_publish"):
        state = await get_usage_state(user_id, usage_type, session)
        items[usage_type] = {
            "usage_type": usage_type,
            "label": USAGE_LABELS.get(usage_type, usage_type),
            "period_type": state.period_type,
            "quota": state.quota,
            "used": state.used,
            "remaining": state.remaining,
            "bonus_remaining": state.bonus_remaining,
            "period_start": state.period_start,
        }
    return {
        "membership_status": "vip" if is_vip else "free",
        "items": items,
    }
