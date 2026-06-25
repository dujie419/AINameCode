import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_session
from admin_auth import encode_admin_token, get_current_admin
from repository.admin_repo import AdminRepository, AdminUserRepository
from models.admin import AdminAuditLog, AdminUser
from models.account import (
    ExpertIncomeRecord,
    ExpertWithdrawal,
    Invoice,
    UserMembership,
    Order,
    PaymentOrder,
    PlatformLedger,
    ReconciliationRecord,
    RefundOrder,
    UsageRecord,
    WalletTransaction,
    ExpertFeeRule,
)
from models.growth import DistributionPartner, PartnerAttribution, PartnerCommissionRecord, PartnerWithdrawal
from models.marketplace import AfterSaleRequest, CommunityCandidate, CommunityPost, CommunityVote, Expert, ExpertOrder, ExpertReview
from models.name_record import NameCandidate, NameRecord
from models.user import User
from schemas.marketplace import ExpertOut
from schemas.marketplace import AfterSaleHandleIn
from schemas.admin import (
    AdminLoginIn,
    AdminLoginOut,
    AdminTokenData,
    BalanceAdjustIn,
    DashboardStatisticsOut,
    MembershipAdjustIn,
    PageOut,
    QuotaAdjustIn,
    UserAdminDetailOut,
    UserAdminOut,
    UserLevelIn,
    UserStatusIn,
)
from services.quota_service import get_active_membership, get_usage_state, quota_summary
from schemas.growth import PartnerOut
from services.partner_commission_service import reverse_partner_commission_for_order
from services.partner_commission_service import settle_due_partner_commissions

router = APIRouter(prefix="/admin", tags=["admin"])


def money(value) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def make_order_no(prefix: str) -> str:
    return f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:8].upper()}"


def require_reason(reason: str) -> str:
    value = (reason or "").strip()
    if not value:
        raise HTTPException(status_code=400, detail="操作原因必填")
    return value


def value_text(value) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(money(value))
    if value is None:
        return ""
    return str(value)


def add_admin_audit(
        session: AsyncSession,
        admin_id: int,
        user_id: int,
        action_type: str,
        target_field: str,
        before_value,
        after_value,
        reason: str,
) -> None:
    session.add(AdminAuditLog(
        admin_id=admin_id,
        user_id=user_id,
        action_type=action_type,
        target_field=target_field,
        before_value=value_text(before_value),
        after_value=value_text(after_value),
        reason=require_reason(reason),
    ))


async def admin_user_detail_out(session: AsyncSession, user: User) -> dict:
    membership = await get_active_membership(user.id, session)
    quota = await quota_summary(user.id, session)
    usage_result = await session.execute(
        select(UsageRecord.usage_type, func.coalesce(func.sum(UsageRecord.amount), 0))
        .where(
            UsageRecord.user_id == user.id,
            UsageRecord.amount > 0,
            UsageRecord.reason.not_like("管理员调整:%"),
        )
        .group_by(UsageRecord.usage_type)
    )
    audit_result = await session.execute(
        select(AdminAuditLog)
        .where(AdminAuditLog.user_id == user.id)
        .order_by(AdminAuditLog.id.desc())
        .limit(20)
    )
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "status": user.status,
        "user_level": getattr(user, "user_level", "normal"),
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "balance": money(user.balance),
        "frozen_balance": money(user.frozen_balance),
        "membership_status": "active" if membership else "inactive",
        "membership_expires_at": membership.expires_at if membership else None,
        "quota_items": quota.get("items", {}),
        "usage_totals": {usage_type: int(total or 0) for usage_type, total in usage_result.all()},
        "audit_logs": [
            {
                "id": item.id,
                "admin_id": item.admin_id,
                "user_id": item.user_id,
                "action_type": item.action_type,
                "target_field": item.target_field,
                "before_value": item.before_value,
                "after_value": item.after_value,
                "reason": item.reason,
                "created_at": item.created_at,
            }
            for item in audit_result.scalars().all()
        ],
    }


async def reverse_expert_income(session: AsyncSession, expert_order: ExpertOrder, reason: str) -> None:
    income = await session.scalar(select(ExpertIncomeRecord).where(ExpertIncomeRecord.order_id == expert_order.id))
    if not income or income.status == "reversed":
        return
    expert = await session.get(Expert, expert_order.expert_id)
    if income.status == "settled" and expert:
        expert_user = await session.scalar(select(User).where(User.id == expert.user_id).with_for_update())
        if expert_user and money(expert_user.balance) >= money(income.actual_income):
            expert_user.balance = money(expert_user.balance) - money(income.actual_income)
            session.add(WalletTransaction(
                user_id=expert.user_id,
                transaction_type="expert_income_reverse",
                amount=-money(income.actual_income),
                balance_after=money(expert_user.balance),
                description=f"专家订单 {expert_order.id} 售后退款收入冲销",
                related_order_id=expert_order.id,
            ))
        else:
            income.status = "clawback_pending"
            income.reverse_reason = reason
            return
    income.status = "reversed"
    income.reversed_at = datetime.now()
    income.reverse_reason = reason
    session.add(PlatformLedger(
        ledger_type="expert_service_fee_reverse",
        order_id=expert_order.id,
        expert_id=expert_order.expert_id,
        user_id=expert_order.user_id,
        amount=-money(income.platform_fee),
        description=reason,
    ))


async def ensure_refund_for_after_sale(session: AsyncSession, item: AfterSaleRequest, reason: str) -> None:
    if not item.order_id:
        return
    order = await session.get(Order, item.order_id)
    if not order:
        return
    exists = await session.scalar(select(RefundOrder).where(RefundOrder.order_id == order.id, RefundOrder.status.in_(["pending", "success"])))
    if exists:
        return
    payment = await session.scalar(
        select(PaymentOrder).where(PaymentOrder.business_type == "order", PaymentOrder.business_id == order.id, PaymentOrder.status == "paid")
    )
    provider = payment.provider if payment else "wallet"
    refund = RefundOrder(
        user_id=order.user_id,
        order_id=order.id,
        payment_order_id=payment.id if payment else None,
        refund_no=make_order_no("RFD"),
        provider=provider,
        amount=money(order.amount),
        reason=reason,
        status="success" if provider == "wallet" else "pending",
        refunded_at=datetime.now() if provider == "wallet" else None,
    )
    session.add(refund)
    if provider == "wallet":
        user = await session.scalar(select(User).where(User.id == order.user_id).with_for_update())
        if user:
            user.balance = money(user.balance) + money(order.amount)
            session.add(WalletTransaction(
                user_id=order.user_id,
                transaction_type="refund",
                amount=money(order.amount),
                balance_after=money(user.balance),
                description=f"售后退款 {order.order_no}",
                related_order_id=order.id,
            ))
    await reverse_partner_commission_for_order(order.id, session, reason)


def admin_expert_to_out(expert: Expert):
    return ExpertOut(
        id=expert.id,
        user_id=expert.user_id,
        name=expert.name,
        avatar=expert.avatar,
        title=expert.title,
        description=expert.description,
        tags=[item for item in expert.tags.split(",") if item],
        price=expert.price,
        experience_years=expert.experience_years,
        status=expert.status,
        rating=expert.rating,
        created_at=expert.created_at,
    )


async def admin_partner_to_out(session: AsyncSession, partner: DistributionPartner) -> PartnerOut:
    register_count = await session.scalar(
        select(func.count(PartnerAttribution.id)).where(PartnerAttribution.partner_id == partner.id)
    ) or 0
    return PartnerOut(
        id=partner.id,
        user_id=partner.user_id,
        partner_type=partner.partner_type,
        name=partner.name,
        contact_phone=partner.contact_phone,
        company_name=partner.company_name,
        address=partner.address,
        description=partner.description,
        partner_code=partner.partner_code,
        qr_payload=partner.qr_payload,
        commission_rate=partner.commission_rate,
        status=partner.status,
        reviewed_at=partner.reviewed_at,
        review_reason=partner.review_reason,
        created_at=partner.created_at,
        register_count=int(register_count),
    )


def admin_partner_commission_out(item: PartnerCommissionRecord) -> dict:
    return {
        "id": item.id,
        "partner_id": item.partner_id,
        "partner_user_id": item.partner_user_id,
        "buyer_user_id": item.buyer_user_id,
        "business_type": item.business_type,
        "business_id": item.business_id,
        "order_id": item.order_id,
        "payment_order_id": item.payment_order_id,
        "base_amount": money(item.base_amount),
        "commission_rate": item.commission_rate,
        "commission_amount": money(item.commission_amount),
        "status": item.status,
        "settlement_due_at": item.settlement_due_at,
        "settled_at": item.settled_at,
        "reversed_at": item.reversed_at,
        "reverse_reason": item.reverse_reason,
        "created_at": item.created_at,
    }


def admin_partner_withdrawal_out(item: PartnerWithdrawal) -> dict:
    return {
        "id": item.id,
        "partner_id": item.partner_id,
        "partner_user_id": item.partner_user_id,
        "withdrawal_no": item.withdrawal_no,
        "amount": money(item.amount),
        "account_name": item.account_name,
        "account_no": item.account_no,
        "bank_name": item.bank_name,
        "status": item.status,
        "reason": item.reason,
        "payment_channel": item.payment_channel,
        "payment_trade_no": item.payment_trade_no,
        "created_at": item.created_at,
        "reviewed_at": item.reviewed_at,
        "paid_at": item.paid_at,
    }


async def admin_name_record_to_out(session: AsyncSession, record: NameRecord) -> dict:
    result = await session.execute(
        select(NameCandidate).where(NameCandidate.record_id == record.id).order_by(NameCandidate.id.asc())
    )
    candidates = [
        {
            "id": item.id,
            "name": item.name,
            "reference": item.reference,
            "moral": item.moral,
            "domain": item.domain,
            "domain_status": item.domain_status,
        }
        for item in result.scalars().all()
    ]
    try:
        content = json.loads(record.result_json or "{}")
    except json.JSONDecodeError:
        content = {}
    return {
        "id": record.id,
        "user_id": record.user_id,
        "thread_id": record.thread_id,
        "naming_type": record.naming_type,
        "source_type": record.source_type,
        "keyword": record.keyword,
        "surname": record.surname,
        "gender": record.gender,
        "length": record.length,
        "feedback": record.feedback,
        "status": record.status,
        "parent_record_id": record.parent_record_id,
        "content": content,
        "candidates": candidates,
        "created_at": record.created_at,
    }


@router.post("/login", response_model=AdminLoginOut)
async def admin_login(
        admin_info: AdminLoginIn,
        session: AsyncSession = Depends(get_session),
):
    admin_repository = AdminRepository(session=session)
    admin = await admin_repository.get_admin_by_username(admin_info.username)
    if not admin:
        raise HTTPException(status_code=400, detail="管理员不存在")
    if admin.status != "active":
        raise HTTPException(status_code=403, detail="管理员账号已禁用")
    if not admin.check_password(admin_info.password):
        raise HTTPException(status_code=400, detail="管理员密码错误")

    return {
        "access_token": encode_admin_token(admin.id, admin.role),
        "token_type": "bearer",
        "role": admin.role,
    }


@router.get("/users", response_model=PageOut)
async def admin_users(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        keyword: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    user_repository = AdminUserRepository(session=session)
    total, users = await user_repository.list_users(page=page, page_size=page_size, keyword=keyword)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [UserAdminOut.model_validate(user, from_attributes=True) for user in users],
    }


@router.get("/users/{user_id}", response_model=UserAdminDetailOut)
async def admin_user_detail(
        user_id: int,
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return await admin_user_detail_out(session, user)


@router.put("/users/{user_id}/status", response_model=UserAdminOut)
async def admin_update_user_status(
        user_id: int,
        data: UserStatusIn,
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    user_repository = AdminUserRepository(session=session)
    user = await user_repository.update_user_status(user_id=user_id, status=data.status)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserAdminOut.model_validate(user, from_attributes=True)


@router.post("/users/{user_id}/balance-adjust", response_model=UserAdminDetailOut)
async def admin_adjust_user_balance(
        user_id: int,
        data: BalanceAdjustIn,
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    reason = require_reason(data.reason)
    amount = money(data.amount)
    if amount == 0:
        raise HTTPException(status_code=400, detail="调整金额不能为 0")
    user = await session.scalar(select(User).where(User.id == user_id).with_for_update())
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    before = money(user.balance)
    after = before + amount
    if after < 0:
        raise HTTPException(status_code=400, detail="余额不足，不能扣减到负数")
    user.balance = after
    session.add(WalletTransaction(
        user_id=user.id,
        transaction_type="admin_adjust",
        amount=amount,
        balance_after=after,
        description=reason,
        related_order_id=None,
    ))
    add_admin_audit(session, admin.admin_id, user.id, "balance_adjust", "balance", before, after, reason)
    await session.commit()
    await session.refresh(user)
    return await admin_user_detail_out(session, user)


@router.post("/users/{user_id}/quota-adjust", response_model=UserAdminDetailOut)
async def admin_adjust_user_quota(
        user_id: int,
        data: QuotaAdjustIn,
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    reason = require_reason(data.reason)
    if data.amount == 0:
        raise HTTPException(status_code=400, detail="调整次数不能为 0")
    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    before_state = await get_usage_state(user.id, data.usage_type, session)
    usage_amount = -data.amount
    after_remaining = max(before_state.remaining + data.amount, 0)
    session.add(UsageRecord(
        user_id=user.id,
        usage_type=data.usage_type,
        amount=usage_amount,
        remaining_quota=after_remaining,
        period_type=before_state.period_type,
        period_start=before_state.period_start,
        reason=f"管理员调整:{reason}",
        related_id=None,
    ))
    add_admin_audit(
        session,
        admin.admin_id,
        user.id,
        "quota_adjust",
        data.usage_type,
        before_state.remaining,
        after_remaining,
        reason,
    )
    await session.commit()
    await session.refresh(user)
    return await admin_user_detail_out(session, user)


@router.post("/users/{user_id}/membership-adjust", response_model=UserAdminDetailOut)
async def admin_adjust_user_membership(
        user_id: int,
        data: MembershipAdjustIn,
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    reason = require_reason(data.reason)
    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    now = datetime.now()
    membership = await get_active_membership(user.id, session)
    before = membership.expires_at if membership else None
    if data.action in ("open", "extend"):
        if membership:
            starts_at = membership.starts_at
            base_time = membership.expires_at if membership.expires_at > now else now
            membership.expires_at = base_time + timedelta(days=data.days)
            membership.status = "active"
            membership.updated_at = now
        else:
            starts_at = now
            membership = UserMembership(
                user_id=user.id,
                plan_id=None,
                status="active",
                starts_at=starts_at,
                expires_at=now + timedelta(days=data.days),
            )
            session.add(membership)
        after = membership.expires_at
    else:
        if membership:
            membership.status = "cancelled"
            membership.updated_at = now
        after = None
    add_admin_audit(session, admin.admin_id, user.id, f"membership_{data.action}", "membership_expires_at", before, after, reason)
    await session.commit()
    await session.refresh(user)
    return await admin_user_detail_out(session, user)


@router.post("/users/{user_id}/level", response_model=UserAdminDetailOut)
async def admin_update_user_level(
        user_id: int,
        data: UserLevelIn,
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    reason = require_reason(data.reason)
    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    before = getattr(user, "user_level", "normal")
    user.user_level = data.user_level
    add_admin_audit(session, admin.admin_id, user.id, "level_update", "user_level", before, user.user_level, reason)
    await session.commit()
    await session.refresh(user)
    return await admin_user_detail_out(session, user)


@router.get("/name-records", response_model=PageOut)
async def admin_name_records(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        user_id: int | None = Query(None),
        naming_type: str | None = Query(None),
        keyword: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(NameRecord)
    count_stmt = select(func.count(NameRecord.id))
    if user_id is not None:
        stmt = stmt.where(NameRecord.user_id == user_id)
        count_stmt = count_stmt.where(NameRecord.user_id == user_id)
    if naming_type:
        stmt = stmt.where(NameRecord.naming_type == naming_type)
        count_stmt = count_stmt.where(NameRecord.naming_type == naming_type)
    if keyword:
        like_keyword = f"%{keyword}%"
        stmt = stmt.where(NameRecord.keyword.like(like_keyword))
        count_stmt = count_stmt.where(NameRecord.keyword.like(like_keyword))
    total = await session.scalar(count_stmt)
    result = await session.execute(
        stmt.order_by(NameRecord.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = [await admin_name_record_to_out(session, record) for record in result.scalars().all()]
    return {
        "total": total or 0,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/dashboard/statistics", response_model=DashboardStatisticsOut)
async def admin_dashboard_statistics(
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    user_total = await session.scalar(select(func.count(User.id))) or 0
    today_new_users = await session.scalar(
        select(func.count(User.id)).where(func.date(User.created_at) == date.today())
    ) or 0
    admin_total = await session.scalar(select(func.count(AdminUser.id))) or 0
    expert_total = await session.scalar(select(func.count(Expert.id))) or 0
    pending_expert_total = await session.scalar(select(func.count(Expert.id)).where(Expert.status == "pending")) or 0
    expert_order_total = await session.scalar(select(func.count(ExpertOrder.id))) or 0
    community_post_total = await session.scalar(select(func.count(CommunityPost.id))) or 0
    community_vote_total = await session.scalar(select(func.count(CommunityVote.id))) or 0
    name_record_total = await session.scalar(select(func.count(NameRecord.id))) or 0
    today_name_count = await session.scalar(
        select(func.count(NameRecord.id)).where(func.date(NameRecord.created_at) == date.today())
    ) or 0
    hot_result = await session.execute(
        select(NameCandidate.name, func.count(NameCandidate.id).label("count"))
        .group_by(NameCandidate.name)
        .order_by(func.count(NameCandidate.id).desc())
        .limit(10)
    )
    return {
        "user_total": user_total,
        "today_new_users": today_new_users,
        "name_record_total": name_record_total,
        "today_name_count": today_name_count,
        "admin_total": admin_total,
        "expert_total": expert_total,
        "pending_expert_total": pending_expert_total,
        "expert_order_total": expert_order_total,
        "community_post_total": community_post_total,
        "community_vote_total": community_vote_total,
        "hot_names_top10": [{"name": name, "vote_count": count} for name, count in hot_result.all()],
    }


@router.get("/experts", response_model=PageOut)
async def admin_experts(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(Expert)
    count_stmt = select(func.count(Expert.id))
    if status:
        stmt = stmt.where(Expert.status == status)
        count_stmt = count_stmt.where(Expert.status == status)
    total = await session.scalar(count_stmt)
    result = await session.execute(stmt.order_by(Expert.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return {"total": total or 0, "page": page, "page_size": page_size, "items": [admin_expert_to_out(x) for x in result.scalars().all()]}


@router.put("/experts/{expert_id}/approve", response_model=ExpertOut)
async def approve_expert(
        expert_id: int,
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        expert = await session.scalar(select(Expert).where(Expert.id == expert_id))
        if not expert:
            raise HTTPException(status_code=404, detail="专家不存在")
        expert.status = "approved"
        user = await session.scalar(select(User).where(User.id == expert.user_id))
        if user:
            user.is_expert = True
    return admin_expert_to_out(expert)


@router.put("/experts/{expert_id}/reject", response_model=ExpertOut)
async def reject_expert(
        expert_id: int,
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        expert = await session.scalar(select(Expert).where(Expert.id == expert_id))
        if not expert:
            raise HTTPException(status_code=404, detail="专家不存在")
        expert.status = "rejected"
        user = await session.scalar(select(User).where(User.id == expert.user_id))
        if user:
            user.is_expert = False
    return admin_expert_to_out(expert)


@router.get("/partners", response_model=PageOut)
async def admin_partners(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        partner_type: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(DistributionPartner)
    count_stmt = select(func.count(DistributionPartner.id))
    if status:
        stmt = stmt.where(DistributionPartner.status == status)
        count_stmt = count_stmt.where(DistributionPartner.status == status)
    if partner_type:
        stmt = stmt.where(DistributionPartner.partner_type == partner_type)
        count_stmt = count_stmt.where(DistributionPartner.partner_type == partner_type)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(
        stmt.order_by(DistributionPartner.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = [await admin_partner_to_out(session, item) for item in result.scalars().all()]
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.put("/partners/{partner_id}/approve", response_model=PartnerOut)
async def approve_partner(
        partner_id: int,
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    partner = await session.get(DistributionPartner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="合伙人申请不存在")
    partner.status = "approved"
    partner.reviewed_at = datetime.now()
    partner.review_reason = None
    await session.commit()
    await session.refresh(partner)
    return await admin_partner_to_out(session, partner)


@router.put("/partners/{partner_id}/reject", response_model=PartnerOut)
async def reject_partner(
        partner_id: int,
        reason: str = Query("审核拒绝"),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    partner = await session.get(DistributionPartner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="合伙人申请不存在")
    partner.status = "rejected"
    partner.reviewed_at = datetime.now()
    partner.review_reason = reason
    await session.commit()
    await session.refresh(partner)
    return await admin_partner_to_out(session, partner)


@router.get("/partner-finance/summary")
async def admin_partner_finance_summary(
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    await settle_due_partner_commissions(session)
    partner_total = await session.scalar(select(func.count(DistributionPartner.id))) or 0
    pending_partner_total = await session.scalar(
        select(func.count(DistributionPartner.id)).where(DistributionPartner.status == "pending")
    ) or 0
    attributed_user_total = await session.scalar(select(func.count(PartnerAttribution.id))) or 0
    pending_commission = await session.scalar(
        select(func.coalesce(func.sum(PartnerCommissionRecord.commission_amount), 0)).where(
            PartnerCommissionRecord.status == "settle_pending"
        )
    ) or 0
    settled_commission = await session.scalar(
        select(func.coalesce(func.sum(PartnerCommissionRecord.commission_amount), 0)).where(
            PartnerCommissionRecord.status == "settled"
        )
    ) or 0
    reversed_commission = await session.scalar(
        select(func.coalesce(func.sum(PartnerCommissionRecord.commission_amount), 0)).where(
            PartnerCommissionRecord.status == "reversed"
        )
    ) or 0
    pending_withdraw = await session.scalar(
        select(func.coalesce(func.sum(PartnerWithdrawal.amount), 0)).where(PartnerWithdrawal.status == "pending")
    ) or 0
    paid_withdraw = await session.scalar(
        select(func.coalesce(func.sum(PartnerWithdrawal.amount), 0)).where(PartnerWithdrawal.status == "paid")
    ) or 0
    await session.commit()
    return {
        "partner_total": int(partner_total),
        "pending_partner_total": int(pending_partner_total),
        "attributed_user_total": int(attributed_user_total),
        "pending_commission": money(pending_commission),
        "settled_commission": money(settled_commission),
        "reversed_commission": money(reversed_commission),
        "pending_withdraw": money(pending_withdraw),
        "paid_withdraw": money(paid_withdraw),
    }


@router.post("/partner-commissions/settle-due")
async def admin_settle_due_partner_commissions(
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    settled_count = await settle_due_partner_commissions(session)
    await session.commit()
    return {"settled_count": settled_count}


@router.get("/partner-commissions", response_model=PageOut)
async def admin_partner_commissions(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        partner_id: int | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(PartnerCommissionRecord)
    count_stmt = select(func.count(PartnerCommissionRecord.id))
    if status:
        stmt = stmt.where(PartnerCommissionRecord.status == status)
        count_stmt = count_stmt.where(PartnerCommissionRecord.status == status)
    if partner_id is not None:
        stmt = stmt.where(PartnerCommissionRecord.partner_id == partner_id)
        count_stmt = count_stmt.where(PartnerCommissionRecord.partner_id == partner_id)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(
        stmt.order_by(PartnerCommissionRecord.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return {"total": total, "page": page, "page_size": page_size, "items": [admin_partner_commission_out(item) for item in result.scalars().all()]}


@router.get("/partner-withdrawals", response_model=PageOut)
async def admin_partner_withdrawals(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(PartnerWithdrawal)
    count_stmt = select(func.count(PartnerWithdrawal.id))
    if status:
        stmt = stmt.where(PartnerWithdrawal.status == status)
        count_stmt = count_stmt.where(PartnerWithdrawal.status == status)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(
        stmt.order_by(PartnerWithdrawal.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return {"total": total, "page": page, "page_size": page_size, "items": [admin_partner_withdrawal_out(item) for item in result.scalars().all()]}


@router.put("/partner-withdrawals/{withdrawal_id}/approve")
async def approve_partner_withdrawal(
        withdrawal_id: int,
        payment_channel: str = Query("manual"),
        payment_trade_no: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    withdrawal = await session.get(PartnerWithdrawal, withdrawal_id)
    if not withdrawal:
        raise HTTPException(status_code=404, detail="合伙人提现申请不存在")
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="提现申请状态不可审核")
    user = await session.scalar(select(User).where(User.id == withdrawal.partner_user_id).with_for_update())
    if user:
        user.frozen_balance = max(money(user.frozen_balance) - money(withdrawal.amount), money(0))
    withdrawal.status = "paid"
    withdrawal.payment_channel = payment_channel
    withdrawal.payment_trade_no = payment_trade_no
    withdrawal.reviewed_at = datetime.now()
    withdrawal.paid_at = datetime.now()
    await session.commit()
    return {"message": "合伙人提现已打款"}


@router.put("/partner-withdrawals/{withdrawal_id}/reject")
async def reject_partner_withdrawal(
        withdrawal_id: int,
        reason: str = Query("审核拒绝"),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    withdrawal = await session.get(PartnerWithdrawal, withdrawal_id)
    if not withdrawal:
        raise HTTPException(status_code=404, detail="合伙人提现申请不存在")
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="提现申请状态不可审核")
    user = await session.scalar(select(User).where(User.id == withdrawal.partner_user_id).with_for_update())
    if user:
        user.frozen_balance = max(money(user.frozen_balance) - money(withdrawal.amount), money(0))
        user.balance = money(user.balance) + money(withdrawal.amount)
        session.add(WalletTransaction(
            user_id=withdrawal.partner_user_id,
            transaction_type="partner_withdraw_return",
            amount=money(withdrawal.amount),
            balance_after=money(user.balance),
            description=f"partner withdrawal rejected {withdrawal.withdrawal_no}",
            related_order_id=None,
        ))
    withdrawal.status = "rejected"
    withdrawal.reason = reason
    withdrawal.reviewed_at = datetime.now()
    await session.commit()
    return {"message": "合伙人提现已拒绝并退回余额"}


@router.get("/expert-orders", response_model=PageOut)
async def admin_expert_orders(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    total = await session.scalar(select(func.count(ExpertOrder.id)))
    result = await session.execute(select(ExpertOrder).order_by(ExpertOrder.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return {"total": total or 0, "page": page, "page_size": page_size, "items": [x.__dict__ for x in result.scalars().all()]}


@router.put("/community/posts/{post_id}/offline")
async def offline_community_post(
        post_id: int,
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        post = await session.scalar(select(CommunityPost).where(CommunityPost.id == post_id))
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        post.status = "offline"
    return {"message": "已下架"}


def admin_obj_dict(item, fields: list[str]) -> dict:
    return {field: getattr(item, field) for field in fields}


@router.get("/payments", response_model=PageOut)
async def admin_payments(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        provider: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(PaymentOrder)
    count_stmt = select(func.count(PaymentOrder.id))
    if status:
        stmt = stmt.where(PaymentOrder.status == status)
        count_stmt = count_stmt.where(PaymentOrder.status == status)
    if provider:
        stmt = stmt.where(PaymentOrder.provider == provider)
        count_stmt = count_stmt.where(PaymentOrder.provider == provider)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(stmt.order_by(PaymentOrder.id.desc()).offset((page - 1) * page_size).limit(page_size))
    fields = ["id", "user_id", "payment_no", "business_type", "business_id", "provider", "provider_trade_no", "amount", "status", "created_at", "paid_at"]
    return {"total": total, "page": page, "page_size": page_size, "items": [admin_obj_dict(item, fields) for item in result.scalars().all()]}


@router.get("/refunds", response_model=PageOut)
async def admin_refunds(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(RefundOrder)
    count_stmt = select(func.count(RefundOrder.id))
    if status:
        stmt = stmt.where(RefundOrder.status == status)
        count_stmt = count_stmt.where(RefundOrder.status == status)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(stmt.order_by(RefundOrder.id.desc()).offset((page - 1) * page_size).limit(page_size))
    fields = ["id", "user_id", "order_id", "payment_order_id", "refund_no", "provider", "amount", "reason", "status", "created_at", "refunded_at"]
    return {"total": total, "page": page, "page_size": page_size, "items": [admin_obj_dict(item, fields) for item in result.scalars().all()]}


@router.get("/withdrawals", response_model=PageOut)
async def admin_withdrawals(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(ExpertWithdrawal)
    count_stmt = select(func.count(ExpertWithdrawal.id))
    if status:
        stmt = stmt.where(ExpertWithdrawal.status == status)
        count_stmt = count_stmt.where(ExpertWithdrawal.status == status)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(stmt.order_by(ExpertWithdrawal.id.desc()).offset((page - 1) * page_size).limit(page_size))
    fields = ["id", "expert_id", "user_id", "withdrawal_no", "amount", "account_name", "account_no", "bank_name", "status", "reason", "payment_channel", "payment_trade_no", "created_at", "reviewed_at", "paid_at"]
    return {"total": total, "page": page, "page_size": page_size, "items": [admin_obj_dict(item, fields) for item in result.scalars().all()]}


@router.get("/expert-finance/summary")
async def admin_expert_finance_summary(
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    service_total = await session.scalar(
        select(func.coalesce(func.sum(ExpertIncomeRecord.amount), 0)).where(
            ExpertIncomeRecord.status.in_(["settle_pending", "settled"])
        )
    ) or 0
    platform_fee_total = await session.scalar(
        select(func.coalesce(func.sum(PlatformLedger.amount), 0)).where(
            PlatformLedger.ledger_type.in_(["expert_service_fee", "expert_service_fee_reverse"])
        )
    ) or 0
    payable_total = await session.scalar(
        select(func.coalesce(func.sum(ExpertIncomeRecord.actual_income), 0)).where(ExpertIncomeRecord.status == "settle_pending")
    ) or 0
    settled_total = await session.scalar(
        select(func.coalesce(func.sum(ExpertIncomeRecord.actual_income), 0)).where(ExpertIncomeRecord.status == "settled")
    ) or 0
    withdrawn_total = await session.scalar(
        select(func.coalesce(func.sum(ExpertWithdrawal.amount), 0)).where(ExpertWithdrawal.status == "paid")
    ) or 0
    pending_withdraw_total = await session.scalar(
        select(func.coalesce(func.sum(ExpertWithdrawal.amount), 0)).where(ExpertWithdrawal.status == "pending")
    ) or 0
    refund_reverse_total = await session.scalar(
        select(func.coalesce(func.sum(RefundOrder.amount), 0)).where(RefundOrder.status.in_(["pending", "success"]))
    ) or 0
    return {
        "expert_service_total": money(service_total),
        "platform_fee_total": money(platform_fee_total),
        "expert_payable_pending": money(payable_total),
        "expert_settled_total": money(settled_total),
        "expert_withdrawn_total": money(withdrawn_total),
        "expert_withdraw_pending": money(pending_withdraw_total),
        "refund_reverse_total": money(refund_reverse_total),
    }


@router.get("/expert-fee-rules", response_model=PageOut)
async def admin_expert_fee_rules(
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(ExpertFeeRule).order_by(ExpertFeeRule.id.desc()))
    fields = ["id", "name", "fee_rate", "status", "created_at"]
    items = [admin_obj_dict(item, fields) for item in result.scalars().all()]
    return {"total": len(items), "page": 1, "page_size": len(items), "items": items}


@router.post("/expert-fee-rules")
async def create_expert_fee_rule(
        fee_rate: Decimal = Query(..., gt=0, lt=1),
        name: str = Query("expert service fee"),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(ExpertFeeRule).where(ExpertFeeRule.status == "active"))
    for item in result.scalars().all():
        item.status = "inactive"
    rule = ExpertFeeRule(name=name, fee_rate=Decimal(str(fee_rate)).quantize(Decimal("0.0001")), status="active")
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return {"id": rule.id, "name": rule.name, "fee_rate": rule.fee_rate, "status": rule.status}


@router.put("/withdrawals/{withdrawal_id}/approve")
async def approve_withdrawal(
        withdrawal_id: int,
        payment_channel: str = Query("manual"),
        payment_trade_no: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    withdrawal = await session.get(ExpertWithdrawal, withdrawal_id)
    if not withdrawal:
        raise HTTPException(status_code=404, detail="提现申请不存在")
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="提现申请状态不可审核")
    user = await session.scalar(select(User).where(User.id == withdrawal.user_id).with_for_update())
    if user:
        user.frozen_balance = max(money(user.frozen_balance) - money(withdrawal.amount), money(0))
    withdrawal.status = "paid"
    withdrawal.payment_channel = payment_channel
    withdrawal.payment_trade_no = payment_trade_no
    withdrawal.reviewed_at = datetime.now()
    withdrawal.paid_at = datetime.now()
    await session.commit()
    return {"message": "提现已打款"}


@router.put("/withdrawals/{withdrawal_id}/reject")
async def reject_withdrawal(
        withdrawal_id: int,
        reason: str = Query("审核拒绝"),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    withdrawal = await session.get(ExpertWithdrawal, withdrawal_id)
    if not withdrawal:
        raise HTTPException(status_code=404, detail="提现申请不存在")
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="提现申请状态不可审核")
    user = await session.scalar(select(User).where(User.id == withdrawal.user_id).with_for_update())
    if user:
        user.frozen_balance = max(money(user.frozen_balance) - money(withdrawal.amount), money(0))
        user.balance = money(user.balance) + money(withdrawal.amount)
        session.add(WalletTransaction(
            user_id=withdrawal.user_id,
            transaction_type="withdraw_return",
            amount=money(withdrawal.amount),
            balance_after=money(user.balance),
            description=f"提现拒绝退回 {withdrawal.withdrawal_no}",
            related_order_id=None,
        ))
    withdrawal.status = "rejected"
    withdrawal.reason = reason
    withdrawal.reviewed_at = datetime.now()
    await session.commit()
    return {"message": "提现已拒绝并退回余额"}


@router.get("/invoices", response_model=PageOut)
async def admin_invoices(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(Invoice)
    count_stmt = select(func.count(Invoice.id))
    if status:
        stmt = stmt.where(Invoice.status == status)
        count_stmt = count_stmt.where(Invoice.status == status)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(stmt.order_by(Invoice.id.desc()).offset((page - 1) * page_size).limit(page_size))
    fields = ["id", "user_id", "order_id", "invoice_no", "title", "tax_no", "amount", "status", "file_url", "created_at", "issued_at"]
    return {"total": total, "page": page, "page_size": page_size, "items": [admin_obj_dict(item, fields) for item in result.scalars().all()]}


@router.put("/invoices/{invoice_id}/issue")
async def issue_invoice(
        invoice_id: int,
        file_url: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    invoice = await session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="发票申请不存在")
    invoice.status = "issued"
    invoice.file_url = file_url
    invoice.issued_at = datetime.now()
    await session.commit()
    return {"message": "发票已开具"}


@router.post("/reconciliations")
async def create_reconciliation(
        provider: str = Query(...),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    today = date.today()
    total_count = await session.scalar(
        select(func.count(PaymentOrder.id)).where(PaymentOrder.provider == provider, PaymentOrder.status == "paid", func.date(PaymentOrder.paid_at) == today)
    ) or 0
    total_amount = await session.scalar(
        select(func.coalesce(func.sum(PaymentOrder.amount), 0)).where(PaymentOrder.provider == provider, PaymentOrder.status == "paid", func.date(PaymentOrder.paid_at) == today)
    ) or 0
    record = ReconciliationRecord(
        provider=provider,
        reconcile_date=datetime.now(),
        total_amount=total_amount,
        total_count=total_count,
        matched_count=total_count,
        mismatch_count=0,
        status="matched",
    )
    session.add(record)
    await session.commit()
    return {"message": "对账完成", "id": record.id, "total_count": total_count, "total_amount": total_amount}


@router.get("/after-sales", response_model=PageOut)
async def admin_after_sales(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(AfterSaleRequest)
    count_stmt = select(func.count(AfterSaleRequest.id))
    if status:
        stmt = stmt.where(AfterSaleRequest.status == status)
        count_stmt = count_stmt.where(AfterSaleRequest.status == status)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(stmt.order_by(AfterSaleRequest.id.desc()).offset((page - 1) * page_size).limit(page_size))
    fields = ["id", "user_id", "expert_id", "expert_order_id", "order_id", "request_no", "request_type", "reason", "description", "status", "resolution", "created_at", "handled_at"]
    return {"total": total, "page": page, "page_size": page_size, "items": [admin_obj_dict(item, fields) for item in result.scalars().all()]}


@router.put("/after-sales/{after_sale_id}/handle")
async def handle_after_sale(
        after_sale_id: int,
        data: AfterSaleHandleIn,
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    item = await session.get(AfterSaleRequest, after_sale_id)
    if not item:
        raise HTTPException(status_code=404, detail="售后单不存在")
    item.status = data.status
    item.resolution = data.resolution
    if data.status in ("approved", "rejected", "closed"):
        item.handled_at = datetime.now()
        expert_order = await session.get(ExpertOrder, item.expert_order_id)
        if expert_order:
            if data.status == "approved":
                await ensure_refund_for_after_sale(session, item, data.resolution or item.reason)
                await reverse_expert_income(session, expert_order, data.resolution or "售后退款")
                expert_order.status = "after_sale_approved"
            elif data.status == "rejected":
                expert_order.status = "after_sale_rejected"
            elif data.status == "closed" and expert_order.status == "after_sale":
                expert_order.status = "delivered"
        if item.order_id:
            order = await session.get(Order, item.order_id)
            if order:
                if data.status == "approved":
                    order.status = "after_sale_approved"
                elif data.status == "rejected":
                    order.status = "after_sale_rejected"
                elif data.status == "closed" and order.status == "after_sale":
                    order.status = "delivered"
    await session.commit()
    return {"message": "售后已处理", "status": item.status}


@router.get("/expert-reviews", response_model=PageOut)
async def admin_expert_reviews(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        admin: AdminTokenData = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(ExpertReview)
    count_stmt = select(func.count(ExpertReview.id))
    if status:
        stmt = stmt.where(ExpertReview.status == status)
        count_stmt = count_stmt.where(ExpertReview.status == status)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(stmt.order_by(ExpertReview.id.desc()).offset((page - 1) * page_size).limit(page_size))
    fields = ["id", "expert_id", "expert_order_id", "user_id", "rating", "content", "reply", "status", "created_at", "replied_at"]
    return {"total": total, "page": page, "page_size": page_size, "items": [admin_obj_dict(item, fields) for item in result.scalars().all()]}
