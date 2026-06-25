import json
import hashlib
import hmac
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from settings import PAYMENT_CALLBACK_SECRET
from models.account import (
    Invoice,
    MembershipOrder,
    MembershipPlan,
    Order,
    PaymentCallbackEvent,
    PaymentOrder,
    PaymentTransaction,
    RechargeOrder,
    RefundOrder,
    UserMembership,
    WalletTransaction,
)
from models.marketplace import Expert, ExpertOrder
from models.user import User
from schemas.account import (
    BalanceOut,
    InvoiceCreateIn,
    InvoiceOut,
    MembershipCreateIn,
    MembershipOrderOut,
    MembershipPlanOut,
    OrderOut,
    PageOut,
    PaymentCallbackIn,
    PaymentOrderOut,
    RechargeCreateIn,
    RechargeOrderOut,
    RefundCreateIn,
    RefundOrderOut,
    UserMembershipOut,
    UserProfileOut,
    UserProfileUpdateIn,
    UsageQuotaSummaryOut,
    VirtualPayOut,
    WalletTransactionOut,
)
from services.quota_service import quota_summary
from services.partner_commission_service import (
    create_partner_commission_for_payment,
    create_partner_commission_for_wallet_order,
    reverse_partner_commission_for_order,
)

router = APIRouter(prefix="/user", tags=["user-center"])
auth_handler = AuthHandler()

AVATAR_DIR = Path("static/uploads/avatar")
AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
ALLOWED_PAYMENT_PROVIDERS = {"virtual", "alipay", "wechat"}
SUCCESS_TRADE_STATUSES = {"success", "paid", "TRADE_SUCCESS"}


def money(value) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def make_order_no(prefix: str = "ORD") -> str:
    return f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:8].upper()}"


def build_pay_url(provider: str, payment_no: str) -> str:
    if provider == "virtual":
        return f"/virtual-pay/{payment_no}"
    return f"/pay/{provider}/{payment_no}"


def normalize_provider(provider: str | None) -> str:
    value = (provider or "virtual").strip().lower()
    if value not in ALLOWED_PAYMENT_PROVIDERS:
        raise HTTPException(status_code=400, detail="Unsupported payment provider")
    return value


def payment_signature(data: PaymentCallbackIn, provider: str) -> str:
    payload = "|".join([
        provider,
        data.payment_no,
        data.provider_trade_no,
        str(money(data.amount)),
        data.trade_status,
        data.event_id,
    ])
    return hmac.new(PAYMENT_CALLBACK_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_payment_signature(data: PaymentCallbackIn, provider: str) -> None:
    if not data.signature:
        raise HTTPException(status_code=401, detail="Missing payment signature")
    expected = payment_signature(data, provider)
    if not hmac.compare_digest(expected, data.signature):
        raise HTTPException(status_code=401, detail="Invalid payment signature")


async def get_current_user(user_id: int, session: AsyncSession) -> User:
    user = await session.scalar(select(User).where(User.id == int(user_id)))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if getattr(user, "status", "active") != "active":
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return user


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


async def is_approved_expert(user_id: int, session: AsyncSession) -> bool:
    expert = await session.scalar(select(Expert).where(Expert.user_id == int(user_id), Expert.status == "approved"))
    return bool(expert)


def profile_out(user: User, expert_enabled: bool, membership: UserMembership | None = None) -> UserProfileOut:
    return UserProfileOut(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        nickname=user.nickname,
        bio=user.bio,
        balance=money(user.balance),
        frozen_balance=money(user.frozen_balance),
        is_expert=bool(user.is_expert or expert_enabled),
        membership_status="active" if membership else "inactive",
        membership_expires_at=membership.expires_at if membership else None,
        created_at=user.created_at,
    )


def membership_plan_out(plan: MembershipPlan) -> MembershipPlanOut:
    return MembershipPlanOut(
        id=plan.id,
        name=plan.name,
        code=plan.code,
        price=money(plan.price),
        duration_days=plan.duration_days,
        description=plan.description,
        status=plan.status,
    )


def membership_order_out(order: MembershipOrder, payment: PaymentOrder, plan: MembershipPlan) -> MembershipOrderOut:
    return MembershipOrderOut(
        membership_order_id=order.id,
        payment_order_id=payment.id,
        payment_no=payment.payment_no,
        provider=payment.provider,
        pay_url=payment.pay_url,
        amount=money(order.amount),
        status=order.status,
        plan=membership_plan_out(plan),
    )


def order_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        user_id=order.user_id,
        order_no=order.order_no,
        order_type=order.order_type,
        amount=money(order.amount),
        status=order.status,
        related_id=order.related_id,
        created_at=order.created_at,
        paid_at=order.paid_at,
        completed_at=order.completed_at,
    )


def transaction_out(item: WalletTransaction) -> WalletTransactionOut:
    return WalletTransactionOut(
        id=item.id,
        user_id=item.user_id,
        transaction_type=item.transaction_type,
        amount=money(item.amount),
        balance_after=money(item.balance_after),
        description=item.description,
        related_order_id=item.related_order_id,
        created_at=item.created_at,
    )


def payment_order_out(item: PaymentOrder) -> PaymentOrderOut:
    return PaymentOrderOut(
        id=item.id,
        user_id=item.user_id,
        payment_no=item.payment_no,
        business_type=item.business_type,
        business_id=item.business_id,
        provider=item.provider,
        provider_trade_no=item.provider_trade_no,
        amount=money(item.amount),
        status=item.status,
        pay_url=item.pay_url,
        created_at=item.created_at,
        paid_at=item.paid_at,
    )


def refund_out(item: RefundOrder) -> RefundOrderOut:
    return RefundOrderOut(
        id=item.id,
        user_id=item.user_id,
        order_id=item.order_id,
        payment_order_id=item.payment_order_id,
        refund_no=item.refund_no,
        provider=item.provider,
        amount=money(item.amount),
        reason=item.reason,
        status=item.status,
        created_at=item.created_at,
        refunded_at=item.refunded_at,
    )


def invoice_out(item: Invoice) -> InvoiceOut:
    return InvoiceOut(
        id=item.id,
        user_id=item.user_id,
        order_id=item.order_id,
        invoice_no=item.invoice_no,
        title=item.title,
        tax_no=item.tax_no,
        amount=money(item.amount),
        status=item.status,
        file_url=item.file_url,
        created_at=item.created_at,
        issued_at=item.issued_at,
    )


async def apply_payment_result(
        payment: PaymentOrder,
        provider: str,
        data: PaymentCallbackIn,
        session: AsyncSession,
) -> dict:
    if payment.status == "paid":
        return {"message": "already paid", "status": payment.status}
    if payment.status not in ("pending", "failed"):
        return {"message": "ignored", "status": payment.status}

    if data.trade_status not in SUCCESS_TRADE_STATUSES:
        payment.status = "failed"
        payment.raw_response = json.dumps(data.model_dump(mode="json"), ensure_ascii=False)
        return {"message": "ignored", "status": payment.status}

    now = datetime.now()
    payment.status = "paid"
    payment.provider_trade_no = data.provider_trade_no
    payment.raw_response = json.dumps(data.model_dump(mode="json"), ensure_ascii=False)
    payment.paid_at = now
    session.add(PaymentTransaction(
        payment_order_id=payment.id,
        user_id=payment.user_id,
        transaction_no=make_order_no("TXN"),
        provider=provider,
        provider_trade_no=data.provider_trade_no,
        amount=money(payment.amount),
        status="success",
        raw_payload=json.dumps(data.raw_payload, ensure_ascii=False),
    ))

    if payment.business_type == "recharge":
        user = await get_current_user(payment.user_id, session)
        recharge = await session.scalar(select(RechargeOrder).where(RechargeOrder.id == payment.business_id))
        if recharge and recharge.status != "paid":
            user.balance = money(user.balance) + money(payment.amount)
            recharge.status = "paid"
            recharge.paid_at = now
            recharge.payment_order_id = payment.id
            session.add(WalletTransaction(
                user_id=payment.user_id,
                transaction_type="recharge",
                amount=money(payment.amount),
                balance_after=money(user.balance),
                description=f"{provider} recharge {payment.payment_no}",
                related_order_id=recharge.id,
            ))
    elif payment.business_type == "order":
        order = await session.scalar(select(Order).where(Order.id == payment.business_id))
        if order and order.status == "pending":
            order.status = "paid"
            order.paid_at = now
            if order.order_type == "expert_service" and order.related_id:
                expert_order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order.related_id))
                if expert_order:
                    expert_order.status = "paid"
            await create_partner_commission_for_payment(payment, session, now)
    elif payment.business_type == "membership":
        member_order = await session.scalar(select(MembershipOrder).where(MembershipOrder.id == payment.business_id))
        if member_order and member_order.status != "paid":
            plan = await session.scalar(select(MembershipPlan).where(MembershipPlan.id == member_order.plan_id))
            if not plan:
                raise HTTPException(status_code=404, detail="Membership plan not found")
            current = await get_active_membership(payment.user_id, session)
            starts_at = current.expires_at if current and current.expires_at > now else now
            expires_at = starts_at + timedelta(days=plan.duration_days)
            if current:
                current.plan_id = plan.id
                current.expires_at = expires_at
                current.updated_at = now
            else:
                session.add(UserMembership(
                    user_id=payment.user_id,
                    plan_id=plan.id,
                    status="active",
                    starts_at=starts_at,
                    expires_at=expires_at,
                ))
            member_order.status = "paid"
            member_order.payment_order_id = payment.id
            member_order.starts_at = starts_at
            member_order.expires_at = expires_at
            member_order.paid_at = now
            await create_partner_commission_for_payment(payment, session, now)
    else:
        raise HTTPException(status_code=400, detail="Unsupported payment business type")

    return {"message": "success", "status": payment.status}


@router.get("/profile", response_model=UserProfileOut)
async def get_profile(
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    user = await get_current_user(user_id, session)
    membership = await get_active_membership(int(user_id), session)
    return profile_out(user, await is_approved_expert(int(user_id), session), membership)


@router.put("/profile", response_model=UserProfileOut)
async def update_profile(
        data: UserProfileUpdateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    user = await get_current_user(user_id, session)
    for field in ("nickname", "phone", "avatar", "bio"):
        value = getattr(data, field)
        if value is not None:
            setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    membership = await get_active_membership(int(user_id), session)
    return profile_out(user, await is_approved_expert(int(user_id), session), membership)


@router.post("/avatar/upload")
async def upload_avatar(
        file: UploadFile = File(...),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    user = await get_current_user(user_id, session)
    suffix = AVATAR_TYPES.get(file.content_type or "")
    if not suffix:
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/webp 头像")
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"user_{user.id}_{uuid4().hex}{suffix}"
    save_path = AVATAR_DIR / filename
    save_path.write_bytes(await file.read())
    avatar_url = f"/static/uploads/avatar/{filename}"
    user.avatar = avatar_url
    await session.commit()
    return {"avatar": avatar_url, "url": avatar_url}


@router.get("/balance", response_model=BalanceOut)
async def get_balance(
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    user = await get_current_user(user_id, session)
    return {"balance": money(user.balance)}


@router.post("/recharge", response_model=RechargeOrderOut)
async def create_recharge_order(
        data: RechargeCreateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    await get_current_user(user_id, session)
    amount = money(data.amount)
    provider = normalize_provider(data.provider)
    order = RechargeOrder(user_id=int(user_id), amount=amount, status="pending", payment_method=provider)
    session.add(order)
    await session.flush()

    payment = PaymentOrder(
        user_id=int(user_id),
        payment_no=make_order_no("PAY"),
        business_type="recharge",
        business_id=order.id,
        provider=provider,
        amount=amount,
        status="pending",
        raw_request=json.dumps({"amount": str(amount), "provider": provider}, ensure_ascii=False),
    )
    payment.pay_url = build_pay_url(provider, payment.payment_no)
    session.add(payment)
    await session.flush()
    order.payment_order_id = payment.id
    await session.commit()
    await session.refresh(order)
    await session.refresh(payment)
    return {
        "recharge_order_id": order.id,
        "payment_order_id": payment.id,
        "payment_no": payment.payment_no,
        "provider": payment.provider,
        "pay_url": payment.pay_url,
        "amount": money(order.amount),
        "status": order.status,
    }


@router.post("/recharge/{order_id}/mock-pay")
async def mock_pay_recharge(order_id: int):
    raise HTTPException(status_code=410, detail="模拟支付已停用，请使用支付渠道回调完成入账")


@router.get("/membership/plans", response_model=list[MembershipPlanOut])
async def list_membership_plans(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(MembershipPlan).where(MembershipPlan.status == "active").order_by(MembershipPlan.price.asc(), MembershipPlan.id.asc())
    )
    return [membership_plan_out(item) for item in result.scalars().all()]


@router.get("/membership/current", response_model=UserMembershipOut)
async def get_current_membership(
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    membership = await get_active_membership(int(user_id), session)
    if not membership:
        return {"status": "inactive"}
    return {
        "status": membership.status,
        "plan_id": membership.plan_id,
        "starts_at": membership.starts_at,
        "expires_at": membership.expires_at,
    }


@router.get("/quota/summary", response_model=UsageQuotaSummaryOut)
async def get_quota_summary(
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    await get_current_user(user_id, session)
    return await quota_summary(int(user_id), session)


@router.post("/membership/orders", response_model=MembershipOrderOut)
async def create_membership_order(
        data: MembershipCreateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    await get_current_user(user_id, session)
    provider = normalize_provider(data.provider)
    plan = await session.scalar(select(MembershipPlan).where(MembershipPlan.id == data.plan_id, MembershipPlan.status == "active"))
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")

    order = MembershipOrder(user_id=int(user_id), plan_id=plan.id, amount=money(plan.price), status="pending")
    session.add(order)
    await session.flush()

    payment = PaymentOrder(
        user_id=int(user_id),
        payment_no=make_order_no("PAY"),
        business_type="membership",
        business_id=order.id,
        provider=provider,
        amount=money(plan.price),
        status="pending",
        raw_request=json.dumps({"plan_id": plan.id, "amount": str(plan.price), "provider": provider}, ensure_ascii=False),
    )
    payment.pay_url = build_pay_url(provider, payment.payment_no)
    session.add(payment)
    await session.flush()
    order.payment_order_id = payment.id
    await session.commit()
    await session.refresh(order)
    await session.refresh(payment)
    return membership_order_out(order, payment, plan)


@router.get("/payments/{payment_no}", response_model=PaymentOrderOut)
async def get_payment_order(
        payment_no: str,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    payment = await session.scalar(
        select(PaymentOrder).where(PaymentOrder.payment_no == payment_no, PaymentOrder.user_id == int(user_id))
    )
    if not payment:
        raise HTTPException(status_code=404, detail="支付单不存在")
    return payment_order_out(payment)


@router.post("/payments/{payment_no}/virtual-pay", response_model=VirtualPayOut)
async def virtual_pay_payment(
        payment_no: str,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    payment = await session.scalar(
        select(PaymentOrder).where(
            PaymentOrder.payment_no == payment_no,
            PaymentOrder.user_id == int(user_id),
            PaymentOrder.provider == "virtual",
        )
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment order not found")
    if payment.status == "paid":
        return {"message": "already paid", "payment": payment_order_out(payment)}
    if payment.status != "pending":
        raise HTTPException(status_code=400, detail="Payment order is not payable")

    callback = PaymentCallbackIn(
        payment_no=payment.payment_no,
        provider_trade_no=make_order_no("VIR"),
        amount=money(payment.amount),
        trade_status="success",
        event_id=make_order_no("EVT"),
        raw_payload={"provider": "virtual", "source": "user_action"},
    )
    callback.signature = payment_signature(callback, "virtual")
    verify_payment_signature(callback, "virtual")
    session.add(PaymentCallbackEvent(
        provider="virtual",
        event_id=callback.event_id,
        payment_no=callback.payment_no,
        status="processed",
        raw_payload=json.dumps(callback.raw_payload, ensure_ascii=False),
    ))
    result = await apply_payment_result(payment, "virtual", callback, session)
    await session.commit()
    await session.refresh(payment)
    return {"message": result["message"], "payment": payment_order_out(payment)}


@router.post("/payments/callback/{provider}")
async def payment_callback(
        provider: str,
        data: PaymentCallbackIn,
        session: AsyncSession = Depends(get_session),
):
    provider = normalize_provider(provider)
    verify_payment_signature(data, provider)
    exists_event = await session.scalar(
        select(PaymentCallbackEvent).where(
            PaymentCallbackEvent.provider == provider,
            PaymentCallbackEvent.event_id == data.event_id,
        )
    )
    if exists_event:
        return {"message": "duplicate", "status": exists_event.status}

    payment = await session.scalar(
        select(PaymentOrder).where(PaymentOrder.payment_no == data.payment_no, PaymentOrder.provider == provider)
    )
    if not payment:
        raise HTTPException(status_code=404, detail="支付单不存在")
    if money(data.amount) != money(payment.amount):
        raise HTTPException(status_code=400, detail="支付金额不一致")

    session.add(PaymentCallbackEvent(
        provider=provider,
        event_id=data.event_id,
        payment_no=data.payment_no,
        status="processed",
        raw_payload=json.dumps(data.raw_payload, ensure_ascii=False),
    ))

    result = await apply_payment_result(payment, provider, data, session)
    await session.commit()
    return result


@router.get("/orders", response_model=PageOut)
async def list_orders(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        order_type: str | None = Query(None),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    await get_current_user(user_id, session)
    stmt = select(Order).where(Order.user_id == int(user_id))
    count_stmt = select(func.count(Order.id)).where(Order.user_id == int(user_id))
    if status:
        stmt = stmt.where(Order.status == status)
        count_stmt = count_stmt.where(Order.status == status)
    if order_type:
        stmt = stmt.where(Order.order_type == order_type)
        count_stmt = count_stmt.where(Order.order_type == order_type)
    total = await session.scalar(count_stmt)
    result = await session.execute(stmt.order_by(Order.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return {"total": total or 0, "page": page, "page_size": page_size, "items": [order_out(item) for item in result.scalars().all()]}


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order_detail(
        order_id: int,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    order = await session.scalar(select(Order).where(Order.id == order_id, Order.user_id == int(user_id)))
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order_out(order)


@router.post("/orders/{order_id}/pay", response_model=OrderOut)
async def pay_order_by_balance(
        order_id: int,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    user = await get_current_user(user_id, session)
    order = await session.scalar(select(Order).where(Order.id == order_id, Order.user_id == int(user_id)))
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="订单不可重复支付")
    if money(user.balance) < money(order.amount):
        raise HTTPException(status_code=400, detail="余额不足")

    user.balance = money(user.balance) - money(order.amount)
    order.status = "paid"
    order.paid_at = datetime.now()
    session.add(WalletTransaction(
        user_id=int(user_id),
        transaction_type="pay",
        amount=-money(order.amount),
        balance_after=money(user.balance),
        description=f"wallet pay order {order.order_no}",
        related_order_id=order.id,
    ))
    if order.order_type == "expert_service" and order.related_id:
        expert_order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order.related_id))
        if expert_order:
            expert_order.status = "paid"
    await create_partner_commission_for_wallet_order(order, session, order.paid_at)
    await session.commit()
    await session.refresh(order)
    return order_out(order)


@router.post("/orders/{order_id}/payment", response_model=PaymentOrderOut)
async def create_order_payment(
        order_id: int,
        provider: str = Query("virtual"),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    provider = normalize_provider(provider)
    order = await session.scalar(select(Order).where(Order.id == order_id, Order.user_id == int(user_id)))
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="当前订单不需要支付")
    exists = await session.scalar(
        select(PaymentOrder).where(
            PaymentOrder.business_type == "order",
            PaymentOrder.business_id == order.id,
            PaymentOrder.provider == provider,
            PaymentOrder.status == "pending",
        )
    )
    if exists:
        return payment_order_out(exists)
    payment = PaymentOrder(
        user_id=int(user_id),
        payment_no=make_order_no("PAY"),
        business_type="order",
        business_id=order.id,
        provider=provider,
        amount=money(order.amount),
        status="pending",
        raw_request=json.dumps({"order_id": order.id, "amount": str(order.amount), "provider": provider}, ensure_ascii=False),
    )
    payment.pay_url = build_pay_url(provider, payment.payment_no)
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment_order_out(payment)


@router.post("/orders/{order_id}/refund", response_model=RefundOrderOut)
async def create_order_refund(
        order_id: int,
        data: RefundCreateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    user = await get_current_user(user_id, session)
    order = await session.scalar(select(Order).where(Order.id == order_id, Order.user_id == int(user_id)))
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status not in ("paid", "processing"):
        raise HTTPException(status_code=400, detail="当前订单不可退款")
    exists = await session.scalar(select(RefundOrder).where(RefundOrder.order_id == order.id, RefundOrder.status.in_(["pending", "success"])))
    if exists:
        return refund_out(exists)
    payment = await session.scalar(
        select(PaymentOrder).where(PaymentOrder.business_type == "order", PaymentOrder.business_id == order.id, PaymentOrder.status == "paid")
    )
    provider = payment.provider if payment else "wallet"
    refund = RefundOrder(
        user_id=int(user_id),
        order_id=order.id,
        payment_order_id=payment.id if payment else None,
        refund_no=make_order_no("RFD"),
        provider=provider,
        amount=money(order.amount),
        reason=data.reason,
        status="success" if provider == "wallet" else "pending",
        refunded_at=datetime.now() if provider == "wallet" else None,
    )
    session.add(refund)
    order.status = "refunded" if provider == "wallet" else "refund_pending"
    if order.order_type == "expert_service" and order.related_id:
        expert_order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order.related_id))
        if expert_order:
            expert_order.status = order.status
    if provider == "wallet":
        user.balance = money(user.balance) + money(order.amount)
        session.add(WalletTransaction(
            user_id=int(user_id),
            transaction_type="refund",
            amount=money(order.amount),
            balance_after=money(user.balance),
            description=f"refund order {order.order_no}",
            related_order_id=order.id,
        ))
    await reverse_partner_commission_for_order(order.id, session, data.reason or f"refund order {order.order_no}")
    await session.commit()
    await session.refresh(refund)
    return refund_out(refund)


@router.get("/wallet/transactions", response_model=PageOut)
async def list_wallet_transactions(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    await get_current_user(user_id, session)
    total = await session.scalar(select(func.count(WalletTransaction.id)).where(WalletTransaction.user_id == int(user_id)))
    result = await session.execute(
        select(WalletTransaction)
        .where(WalletTransaction.user_id == int(user_id))
        .order_by(WalletTransaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {"total": total or 0, "page": page, "page_size": page_size, "items": [transaction_out(item) for item in result.scalars().all()]}


@router.post("/invoices", response_model=InvoiceOut)
async def create_invoice(
        data: InvoiceCreateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    amount = data.amount
    if data.order_id:
        order = await session.scalar(select(Order).where(Order.id == data.order_id, Order.user_id == int(user_id)))
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        if order.status not in ("paid", "completed"):
            raise HTTPException(status_code=400, detail="仅已支付或已完成订单可申请发票")
        amount = money(order.amount)
    if amount is None:
        raise HTTPException(status_code=400, detail="缺少开票金额")
    invoice = Invoice(
        user_id=int(user_id),
        order_id=data.order_id,
        invoice_no=make_order_no("INV"),
        title=data.title,
        tax_no=data.tax_no,
        amount=money(amount),
        status="pending",
    )
    session.add(invoice)
    await session.commit()
    await session.refresh(invoice)
    return invoice_out(invoice)


def build_order_for_related(user_id: int, order_type: str, amount: Decimal, related_id: int | None = None) -> Order:
    return Order(
        user_id=int(user_id),
        order_no=make_order_no(),
        order_type=order_type,
        amount=money(amount),
        status="pending",
        related_id=related_id,
    )
