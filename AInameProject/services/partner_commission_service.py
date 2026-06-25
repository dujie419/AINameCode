from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.account import PaymentOrder, PlatformLedger, WalletTransaction
from models.growth import DistributionPartner, PartnerAttribution, PartnerCommissionRecord, PartnerWithdrawal
from models.user import User

COMMISSION_SETTLEMENT_WAIT_DAYS = 7
COMMISSION_BUSINESS_TYPES = {"order", "membership"}


def money(value) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def make_partner_withdrawal_no() -> str:
    return f"PWD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:8].upper()}"


async def create_partner_commission_for_payment(
        payment: PaymentOrder,
        session: AsyncSession,
        paid_at: datetime | None = None,
) -> PartnerCommissionRecord | None:
    if payment.business_type not in COMMISSION_BUSINESS_TYPES:
        return None

    exists = await session.scalar(
        select(PartnerCommissionRecord).where(
            PartnerCommissionRecord.business_type == payment.business_type,
            PartnerCommissionRecord.business_id == int(payment.business_id),
        )
    )
    if exists:
        return exists

    attribution = await session.scalar(select(PartnerAttribution).where(PartnerAttribution.user_id == int(payment.user_id)))
    if not attribution:
        return None
    partner = await session.scalar(
        select(DistributionPartner).where(
            DistributionPartner.id == attribution.partner_id,
            DistributionPartner.status == "approved",
        )
    )
    if not partner:
        return None

    base_amount = money(payment.amount)
    if base_amount <= 0:
        return None
    commission_rate = Decimal(str(partner.commission_rate)).quantize(Decimal("0.0001"))
    commission_amount = money(base_amount * commission_rate)
    if commission_amount <= 0:
        return None

    now = paid_at or payment.paid_at or datetime.now()
    record = PartnerCommissionRecord(
        partner_id=partner.id,
        partner_user_id=partner.user_id,
        buyer_user_id=payment.user_id,
        attribution_id=attribution.id,
        business_type=payment.business_type,
        business_id=payment.business_id,
        order_id=payment.business_id if payment.business_type == "order" else None,
        payment_order_id=payment.id,
        base_amount=base_amount,
        commission_rate=commission_rate,
        commission_amount=commission_amount,
        status="settle_pending",
        settlement_due_at=now + timedelta(days=COMMISSION_SETTLEMENT_WAIT_DAYS),
    )
    session.add(record)
    return record


async def create_partner_commission_for_wallet_order(
        order,
        session: AsyncSession,
        paid_at: datetime | None = None,
) -> PartnerCommissionRecord | None:
    exists = await session.scalar(
        select(PartnerCommissionRecord).where(
            PartnerCommissionRecord.business_type == "order",
            PartnerCommissionRecord.business_id == int(order.id),
        )
    )
    if exists:
        return exists
    attribution = await session.scalar(select(PartnerAttribution).where(PartnerAttribution.user_id == int(order.user_id)))
    if not attribution:
        return None
    partner = await session.scalar(
        select(DistributionPartner).where(
            DistributionPartner.id == attribution.partner_id,
            DistributionPartner.status == "approved",
        )
    )
    if not partner:
        return None
    base_amount = money(order.amount)
    commission_rate = Decimal(str(partner.commission_rate)).quantize(Decimal("0.0001"))
    commission_amount = money(base_amount * commission_rate)
    if commission_amount <= 0:
        return None
    now = paid_at or datetime.now()
    record = PartnerCommissionRecord(
        partner_id=partner.id,
        partner_user_id=partner.user_id,
        buyer_user_id=order.user_id,
        attribution_id=attribution.id,
        business_type="order",
        business_id=order.id,
        order_id=order.id,
        payment_order_id=None,
        base_amount=base_amount,
        commission_rate=commission_rate,
        commission_amount=commission_amount,
        status="settle_pending",
        settlement_due_at=now + timedelta(days=COMMISSION_SETTLEMENT_WAIT_DAYS),
    )
    session.add(record)
    return record


async def reverse_partner_commission_for_order(
        order_id: int,
        session: AsyncSession,
        reason: str,
) -> PartnerCommissionRecord | None:
    record = await session.scalar(
        select(PartnerCommissionRecord).where(
            PartnerCommissionRecord.business_type == "order",
            PartnerCommissionRecord.business_id == int(order_id),
        )
    )
    if not record or record.status == "reversed":
        return record
    now = datetime.now()
    if record.status == "settled":
        partner_user = await session.scalar(select(User).where(User.id == record.partner_user_id).with_for_update())
        if partner_user and money(partner_user.balance) >= money(record.commission_amount):
            partner_user.balance = money(partner_user.balance) - money(record.commission_amount)
            session.add(WalletTransaction(
                user_id=record.partner_user_id,
                transaction_type="partner_commission_reverse",
                amount=-money(record.commission_amount),
                balance_after=money(partner_user.balance),
                description=f"partner commission reversed for order {order_id}",
                related_order_id=order_id,
            ))
            record.status = "reversed"
            record.reversed_at = now
        else:
            record.status = "clawback_pending"
    else:
        record.status = "reversed"
        record.reversed_at = now
    record.reverse_reason = reason
    session.add(PlatformLedger(
        ledger_type="partner_commission_reverse",
        order_id=order_id,
        user_id=record.buyer_user_id,
        amount=-money(record.commission_amount),
        description=reason,
    ))
    return record


async def settle_due_partner_commissions(
        session: AsyncSession,
        partner_id: int | None = None,
) -> int:
    now = datetime.now()
    stmt = select(PartnerCommissionRecord).where(
        PartnerCommissionRecord.status == "settle_pending",
        PartnerCommissionRecord.settlement_due_at <= now,
    )
    if partner_id is not None:
        stmt = stmt.where(PartnerCommissionRecord.partner_id == int(partner_id))
    result = await session.execute(stmt.order_by(PartnerCommissionRecord.id.asc()))
    settled = 0
    for record in result.scalars().all():
        partner_user = await session.scalar(select(User).where(User.id == record.partner_user_id).with_for_update())
        if not partner_user:
            continue
        partner_user.balance = money(partner_user.balance) + money(record.commission_amount)
        record.status = "settled"
        record.settled_at = now
        session.add(WalletTransaction(
            user_id=record.partner_user_id,
            transaction_type="partner_commission",
            amount=money(record.commission_amount),
            balance_after=money(partner_user.balance),
            description=f"partner commission settled {record.business_type}:{record.business_id}",
            related_order_id=record.order_id,
        ))
        session.add(PlatformLedger(
            ledger_type="partner_commission_cost",
            order_id=record.order_id,
            user_id=record.buyer_user_id,
            amount=money(record.commission_amount),
            description=f"partner commission {record.id}",
        ))
        settled += 1
    return settled


async def partner_finance_summary(partner: DistributionPartner, session: AsyncSession) -> dict:
    register_count = await session.scalar(select(func.count(PartnerAttribution.id)).where(PartnerAttribution.partner_id == partner.id)) or 0
    commission_total = await session.scalar(
        select(func.coalesce(func.sum(PartnerCommissionRecord.commission_amount), 0)).where(
            PartnerCommissionRecord.partner_id == partner.id,
            PartnerCommissionRecord.status.in_(["settle_pending", "settled", "clawback_pending"]),
        )
    ) or 0
    pending_commission = await session.scalar(
        select(func.coalesce(func.sum(PartnerCommissionRecord.commission_amount), 0)).where(
            PartnerCommissionRecord.partner_id == partner.id,
            PartnerCommissionRecord.status == "settle_pending",
        )
    ) or 0
    settled_commission = await session.scalar(
        select(func.coalesce(func.sum(PartnerCommissionRecord.commission_amount), 0)).where(
            PartnerCommissionRecord.partner_id == partner.id,
            PartnerCommissionRecord.status == "settled",
        )
    ) or 0
    reversed_commission = await session.scalar(
        select(func.coalesce(func.sum(PartnerCommissionRecord.commission_amount), 0)).where(
            PartnerCommissionRecord.partner_id == partner.id,
            PartnerCommissionRecord.status == "reversed",
        )
    ) or 0
    user = await session.get(User, partner.user_id)
    return {
        "register_count": int(register_count),
        "commission_total": money(commission_total),
        "pending_commission": money(pending_commission),
        "settled_commission": money(settled_commission),
        "reversed_commission": money(reversed_commission),
        "available_balance": money(user.balance if user else 0),
        "frozen_balance": money(user.frozen_balance if user else 0),
    }


async def create_partner_withdrawal(
        partner: DistributionPartner,
        amount: Decimal,
        account_name: str,
        account_no: str,
        bank_name: str,
        session: AsyncSession,
) -> PartnerWithdrawal:
    user = await session.scalar(select(User).where(User.id == partner.user_id).with_for_update())
    if not user:
        raise HTTPException(status_code=404, detail="合伙人用户不存在")
    amount = money(amount)
    if money(user.balance) < amount:
        raise HTTPException(status_code=400, detail="可提现余额不足")
    user.balance = money(user.balance) - amount
    user.frozen_balance = money(user.frozen_balance) + amount
    withdrawal = PartnerWithdrawal(
        partner_id=partner.id,
        partner_user_id=partner.user_id,
        withdrawal_no=make_partner_withdrawal_no(),
        amount=amount,
        account_name=account_name,
        account_no=account_no,
        bank_name=bank_name,
        status="pending",
    )
    session.add(withdrawal)
    session.add(WalletTransaction(
        user_id=partner.user_id,
        transaction_type="partner_withdraw_freeze",
        amount=-amount,
        balance_after=money(user.balance),
        description=f"partner withdrawal {withdrawal.withdrawal_no}",
        related_order_id=None,
    ))
    return withdrawal
