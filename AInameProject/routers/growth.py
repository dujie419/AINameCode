from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from models.growth import (
    DistributionPartner,
    InvitationRewardRecord,
    PartnerAttribution,
    PartnerCommissionRecord,
    PartnerWithdrawal,
    ReferralRelation,
    UserQuotaGrant,
)
from models.user import User
from schemas.growth import (
    PartnerApplyIn,
    PartnerCommissionOut,
    PartnerFinanceSummaryOut,
    PartnerOut,
    PartnerWithdrawalCreateIn,
    PartnerWithdrawalOut,
)
from services.invite_service import get_or_create_invite_code, partner_qr_payload, random_partner_code
from services.partner_commission_service import (
    create_partner_withdrawal,
    partner_finance_summary,
    settle_due_partner_commissions,
)

router = APIRouter(prefix="/growth", tags=["growth"])
auth_handler = AuthHandler()


def partner_type_rate(partner_type: str):
    return Decimal({
        "maternal_store": "0.1000",
        "business_agent": "0.1500",
    }.get(partner_type, "0.1000"))


async def partner_out(partner: DistributionPartner, session: AsyncSession) -> PartnerOut:
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


def invitee_out(user: User | None, relation: ReferralRelation) -> dict:
    return {
        "id": relation.id,
        "invitee_user_id": relation.invitee_user_id,
        "invitee_username": user.username if user else "",
        "invitee_email": user.email if user else "",
        "reward_status": relation.reward_status,
        "registered_at": relation.registered_at,
        "rewarded_at": relation.rewarded_at,
    }


def attribution_out(user: User | None, item: PartnerAttribution) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "username": user.username if user else "",
        "email": user.email if user else "",
        "partner_code": item.partner_code,
        "source": item.source,
        "first_event": item.first_event,
        "created_at": item.created_at,
    }


def commission_out(item: PartnerCommissionRecord) -> PartnerCommissionOut:
    return PartnerCommissionOut(
        id=item.id,
        partner_id=item.partner_id,
        partner_user_id=item.partner_user_id,
        buyer_user_id=item.buyer_user_id,
        business_type=item.business_type,
        business_id=item.business_id,
        order_id=item.order_id,
        payment_order_id=item.payment_order_id,
        base_amount=item.base_amount,
        commission_rate=item.commission_rate,
        commission_amount=item.commission_amount,
        status=item.status,
        settlement_due_at=item.settlement_due_at,
        settled_at=item.settled_at,
        reversed_at=item.reversed_at,
        reverse_reason=item.reverse_reason,
        created_at=item.created_at,
    )


def withdrawal_out(item: PartnerWithdrawal) -> PartnerWithdrawalOut:
    return PartnerWithdrawalOut(
        id=item.id,
        partner_id=item.partner_id,
        partner_user_id=item.partner_user_id,
        withdrawal_no=item.withdrawal_no,
        amount=item.amount,
        account_name=item.account_name,
        account_no=item.account_no,
        bank_name=item.bank_name,
        status=item.status,
        reason=item.reason,
        payment_channel=item.payment_channel,
        payment_trade_no=item.payment_trade_no,
        created_at=item.created_at,
        reviewed_at=item.reviewed_at,
        paid_at=item.paid_at,
    )


@router.get("/invite/summary")
async def invite_summary(
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    invite_code = await get_or_create_invite_code(int(user_id), session)
    invited_count = await session.scalar(
        select(func.count(ReferralRelation.id)).where(ReferralRelation.inviter_user_id == int(user_id))
    ) or 0
    rewarded_count = await session.scalar(
        select(func.count(ReferralRelation.id)).where(
            ReferralRelation.inviter_user_id == int(user_id),
            ReferralRelation.reward_status == "granted",
        )
    ) or 0
    reward_total = await session.scalar(
        select(func.coalesce(func.sum(InvitationRewardRecord.amount), 0)).where(
            InvitationRewardRecord.reward_target_user_id == int(user_id),
            InvitationRewardRecord.status == "granted",
        )
    ) or 0
    bonus_remaining = await session.scalar(
        select(func.coalesce(func.sum(UserQuotaGrant.total_amount - UserQuotaGrant.used_amount), 0)).where(
            UserQuotaGrant.user_id == int(user_id),
            UserQuotaGrant.usage_type == "name_generate",
            UserQuotaGrant.status == "active",
            UserQuotaGrant.total_amount > UserQuotaGrant.used_amount,
            ((UserQuotaGrant.expires_at.is_(None)) | (UserQuotaGrant.expires_at > datetime.now())),
        )
    ) or 0
    await session.commit()
    return {
        "invite_code": invite_code.code,
        "invited_count": int(invited_count),
        "rewarded_count": int(rewarded_count),
        "reward_total": int(reward_total),
        "bonus_remaining": int(bonus_remaining),
    }


@router.get("/invite/records")
async def invite_records(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    count_stmt = select(func.count(ReferralRelation.id)).where(ReferralRelation.inviter_user_id == int(user_id))
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(
        select(ReferralRelation, User)
        .join(User, User.id == ReferralRelation.invitee_user_id, isouter=True)
        .where(ReferralRelation.inviter_user_id == int(user_id))
        .order_by(ReferralRelation.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "total": int(total),
        "page": page,
        "page_size": page_size,
        "items": [invitee_out(user, relation) for relation, user in result.all()],
    }


@router.post("/partner/apply", response_model=PartnerOut)
async def apply_partner(
        data: PartnerApplyIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    exists = await session.scalar(select(DistributionPartner).where(DistributionPartner.user_id == int(user_id)))
    if exists:
        if exists.status in ("pending", "approved"):
            return await partner_out(exists, session)
        exists.partner_type = data.partner_type
        exists.name = data.name
        exists.contact_phone = data.contact_phone
        exists.company_name = data.company_name
        exists.address = data.address
        exists.description = data.description
        exists.commission_rate = partner_type_rate(data.partner_type)
        exists.status = "pending"
        exists.reviewed_at = None
        exists.review_reason = None
        exists.updated_at = datetime.now()
        partner = exists
    else:
        code = await random_partner_code(session)
        partner = DistributionPartner(
            user_id=int(user_id),
            partner_type=data.partner_type,
            name=data.name,
            contact_phone=data.contact_phone,
            company_name=data.company_name,
            address=data.address,
            description=data.description,
            partner_code=code,
            qr_payload=partner_qr_payload(code),
            commission_rate=partner_type_rate(data.partner_type),
            status="pending",
        )
        session.add(partner)
    await session.commit()
    await session.refresh(partner)
    return await partner_out(partner, session)


@router.get("/partner/profile", response_model=PartnerOut | None)
async def get_partner_profile(
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    partner = await session.scalar(select(DistributionPartner).where(DistributionPartner.user_id == int(user_id)))
    if not partner:
        return None
    return await partner_out(partner, session)


@router.get("/partner/attributions")
async def list_partner_attributions(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    partner = await session.scalar(select(DistributionPartner).where(DistributionPartner.user_id == int(user_id)))
    if not partner:
        return {"total": 0, "page": page, "page_size": page_size, "items": []}
    total = await session.scalar(select(func.count(PartnerAttribution.id)).where(PartnerAttribution.partner_id == partner.id)) or 0
    result = await session.execute(
        select(PartnerAttribution, User)
        .join(User, User.id == PartnerAttribution.user_id, isouter=True)
        .where(PartnerAttribution.partner_id == partner.id)
        .order_by(PartnerAttribution.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "total": int(total),
        "page": page,
        "page_size": page_size,
        "items": [attribution_out(user, item) for item, user in result.all()],
    }


@router.get("/partner/finance/summary", response_model=PartnerFinanceSummaryOut)
async def get_partner_finance_summary(
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    partner = await session.scalar(select(DistributionPartner).where(DistributionPartner.user_id == int(user_id)))
    if not partner:
        return PartnerFinanceSummaryOut()
    await settle_due_partner_commissions(session, partner.id)
    await session.commit()
    return await partner_finance_summary(partner, session)


@router.get("/partner/commissions")
async def list_partner_commissions(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    partner = await session.scalar(select(DistributionPartner).where(DistributionPartner.user_id == int(user_id)))
    if not partner:
        return {"total": 0, "page": page, "page_size": page_size, "items": []}
    stmt = select(PartnerCommissionRecord).where(PartnerCommissionRecord.partner_id == partner.id)
    count_stmt = select(func.count(PartnerCommissionRecord.id)).where(PartnerCommissionRecord.partner_id == partner.id)
    if status:
        stmt = stmt.where(PartnerCommissionRecord.status == status)
        count_stmt = count_stmt.where(PartnerCommissionRecord.status == status)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(
        stmt.order_by(PartnerCommissionRecord.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return {"total": int(total), "page": page, "page_size": page_size, "items": [commission_out(item) for item in result.scalars().all()]}


@router.post("/partner/commissions/settle-due")
async def settle_my_due_partner_commissions(
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    partner = await session.scalar(select(DistributionPartner).where(DistributionPartner.user_id == int(user_id)))
    if not partner:
        return {"settled_count": 0}
    settled_count = await settle_due_partner_commissions(session, partner.id)
    await session.commit()
    return {"settled_count": settled_count}


@router.post("/partner/withdrawals", response_model=PartnerWithdrawalOut)
async def create_my_partner_withdrawal(
        data: PartnerWithdrawalCreateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    partner = await session.scalar(
        select(DistributionPartner).where(DistributionPartner.user_id == int(user_id), DistributionPartner.status == "approved")
    )
    if not partner:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="当前用户不是已审核合伙人")
    await settle_due_partner_commissions(session, partner.id)
    withdrawal = await create_partner_withdrawal(
        partner=partner,
        amount=data.amount,
        account_name=data.account_name,
        account_no=data.account_no,
        bank_name=data.bank_name,
        session=session,
    )
    await session.commit()
    await session.refresh(withdrawal)
    return withdrawal_out(withdrawal)


@router.get("/partner/withdrawals")
async def list_my_partner_withdrawals(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    partner = await session.scalar(select(DistributionPartner).where(DistributionPartner.user_id == int(user_id)))
    if not partner:
        return {"total": 0, "page": page, "page_size": page_size, "items": []}
    total = await session.scalar(select(func.count(PartnerWithdrawal.id)).where(PartnerWithdrawal.partner_id == partner.id)) or 0
    result = await session.execute(
        select(PartnerWithdrawal)
        .where(PartnerWithdrawal.partner_id == partner.id)
        .order_by(PartnerWithdrawal.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {"total": int(total), "page": page, "page_size": page_size, "items": [withdrawal_out(item) for item in result.scalars().all()]}
