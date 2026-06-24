from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from models.account import ExpertIncomeRecord, ExpertWithdrawal, Order, PlatformLedger, WalletTransaction
from models.marketplace import AfterSaleRequest, Expert, ExpertOrder, ExpertReview
from models.user import User
from schemas.account import (
    ExpertCenterProfileOut,
    ExpertIncomeOut,
    ExpertProfileUpdateIn,
    ExpertStatisticsOut,
    ExpertWithdrawalCreateIn,
    ExpertWithdrawalOut,
    PageOut,
)
from schemas.marketplace import AfterSaleOut, ExpertReviewOut, ExpertReviewReplyIn

router = APIRouter(tags=["expert-center"])
auth_handler = AuthHandler()
SETTLEMENT_WAIT_DAYS = 7


def money(value) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def parse_tags(tags: str | None) -> list[str]:
    return [item for item in (tags or "").split(",") if item]


async def get_current_expert(user_id: int, session: AsyncSession) -> Expert:
    expert = await session.scalar(select(Expert).where(Expert.user_id == int(user_id), Expert.status == "approved"))
    if not expert:
        raise HTTPException(status_code=403, detail="当前用户不是已审核专家，请先申请成为专家")
    return expert


async def expert_income_total(expert_id: int, session: AsyncSession) -> Decimal:
    value = await session.scalar(
        select(func.coalesce(func.sum(ExpertIncomeRecord.actual_income), 0)).where(ExpertIncomeRecord.expert_id == expert_id)
    )
    return money(value)


async def expert_profile_out(expert: Expert, session: AsyncSession) -> ExpertCenterProfileOut:
    total_orders = await session.scalar(select(func.count(ExpertOrder.id)).where(ExpertOrder.expert_id == expert.id)) or 0
    completed_orders = await session.scalar(
        select(func.count(ExpertOrder.id)).where(ExpertOrder.expert_id == expert.id, ExpertOrder.status.in_(["delivered", "settled"]))
    ) or 0
    income = await expert_income_total(expert.id, session)
    expert_user = await session.scalar(select(User).where(User.id == expert.user_id).with_for_update())
    return ExpertCenterProfileOut(
        expert_id=expert.id,
        user_id=expert.user_id,
        name=expert.name,
        avatar=expert.avatar,
        title=expert.title,
        description=expert.description,
        tags=parse_tags(expert.tags),
        price=money(expert.price),
        rating=float(expert.rating or 0),
        status=expert.status,
        total_orders=total_orders,
        completed_orders=completed_orders,
        total_income=income,
        available_balance=money(expert_user.balance if expert_user else 0),
        frozen_balance=money(expert_user.frozen_balance if expert_user else 0),
    )


def expert_order_item(order: ExpertOrder, main_order: Order | None = None) -> dict:
    return {
        "id": order.id,
        "user_id": order.user_id,
        "expert_id": order.expert_id,
        "name_record_id": order.name_record_id,
        "amount": money(order.amount),
        "fee_rate_snapshot": order.fee_rate_snapshot,
        "platform_fee": money(order.platform_fee),
        "expert_income": money(order.expert_income),
        "status": order.status,
        "report_url": order.report_url,
        "report_summary": order.report_summary,
        "report_analysis": order.report_analysis,
        "report_suggestions": order.report_suggestions,
        "delivered_at": order.delivered_at,
        "confirmed_at": order.confirmed_at,
        "settlement_due_at": order.settlement_due_at,
        "settled_at": order.settled_at,
        "created_at": order.created_at,
        "order_id": main_order.id if main_order else None,
        "order_no": main_order.order_no if main_order else None,
    }


def income_out(item: ExpertIncomeRecord) -> ExpertIncomeOut:
    return ExpertIncomeOut(
        id=item.id,
        expert_id=item.expert_id,
        user_id=item.user_id,
        order_id=item.order_id,
        amount=money(item.amount),
        platform_fee=money(item.platform_fee),
        actual_income=money(item.actual_income),
        status=item.status,
        settled_at=item.settled_at,
        reversed_at=item.reversed_at,
        reverse_reason=item.reverse_reason,
        created_at=item.created_at,
    )


def withdrawal_out(item: ExpertWithdrawal) -> ExpertWithdrawalOut:
    return ExpertWithdrawalOut(
        id=item.id,
        expert_id=item.expert_id,
        user_id=item.user_id,
        withdrawal_no=item.withdrawal_no,
        amount=money(item.amount),
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


def review_to_out(review: ExpertReview) -> ExpertReviewOut:
    return ExpertReviewOut(
        id=review.id,
        expert_id=review.expert_id,
        expert_order_id=review.expert_order_id,
        user_id=review.user_id,
        rating=review.rating,
        content=review.content,
        reply=review.reply,
        status=review.status,
        created_at=review.created_at,
        replied_at=review.replied_at,
    )


def after_sale_to_out(item: AfterSaleRequest) -> AfterSaleOut:
    return AfterSaleOut(
        id=item.id,
        user_id=item.user_id,
        expert_id=item.expert_id,
        expert_order_id=item.expert_order_id,
        order_id=item.order_id,
        request_no=item.request_no,
        request_type=item.request_type,
        reason=item.reason,
        description=item.description,
        status=item.status,
        resolution=item.resolution,
        created_at=item.created_at,
        handled_at=item.handled_at,
    )


def make_withdrawal_no() -> str:
    return f"WDR{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:8].upper()}"


async def ensure_pending_income(
        session: AsyncSession,
        expert: Expert,
        order: ExpertOrder,
        main_order: Order,
) -> ExpertIncomeRecord:
    exists = await session.scalar(select(ExpertIncomeRecord).where(ExpertIncomeRecord.order_id == order.id))
    if exists:
        return exists
    record = ExpertIncomeRecord(
        expert_id=expert.id,
        user_id=order.user_id,
        order_id=order.id,
        amount=money(main_order.amount),
        platform_fee=money(order.platform_fee),
        actual_income=money(order.expert_income),
        status="settle_pending",
    )
    session.add(record)
    return record


async def settle_expert_order(session: AsyncSession, expert: Expert, order: ExpertOrder, reason: str) -> bool:
    income = await session.scalar(select(ExpertIncomeRecord).where(ExpertIncomeRecord.order_id == order.id))
    if not income or income.status != "settle_pending":
        return False
    expert_user = await session.scalar(select(User).where(User.id == expert.user_id).with_for_update())
    if not expert_user:
        raise HTTPException(status_code=404, detail="专家用户不存在")
    now = datetime.now()
    expert_user.balance = money(expert_user.balance) + money(income.actual_income)
    income.status = "settled"
    income.settled_at = now
    order.status = "settled"
    order.settled_at = now
    session.add(WalletTransaction(
        user_id=expert.user_id,
        transaction_type="expert_income",
        amount=money(income.actual_income),
        balance_after=money(expert_user.balance),
        description=f"涓撳璁㈠崟 {order.id} 缁撶畻鏀跺叆",
        related_order_id=order.id,
    ))
    session.add(PlatformLedger(
        ledger_type="expert_service_fee",
        order_id=order.id,
        expert_id=expert.id,
        user_id=order.user_id,
        amount=money(income.platform_fee),
        description=reason,
    ))
    return True


@router.get("/expert/profile", response_model=ExpertCenterProfileOut)
async def get_expert_profile(
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    return await expert_profile_out(expert, session)


@router.put("/expert/profile", response_model=ExpertCenterProfileOut)
async def update_expert_profile(
        data: ExpertProfileUpdateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    for field in ("name", "avatar", "title", "description", "price"):
        value = getattr(data, field)
        if value is not None:
            setattr(expert, field, value)
    if data.tags is not None:
        expert.tags = ",".join(data.tags)
    await session.commit()
    await session.refresh(expert)
    return await expert_profile_out(expert, session)


@router.get("/expert/center/statistics", response_model=ExpertStatisticsOut)
async def expert_statistics(
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    first_day = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    pending_orders = await session.scalar(
        select(func.count(ExpertOrder.id)).where(ExpertOrder.expert_id == expert.id, ExpertOrder.status == "paid")
    ) or 0
    completed_orders = await session.scalar(
        select(func.count(ExpertOrder.id)).where(ExpertOrder.expert_id == expert.id, ExpertOrder.status.in_(["delivered", "settled"]))
    ) or 0
    total_income = await expert_income_total(expert.id, session)
    expert_user = await session.scalar(select(User).where(User.id == expert.user_id))
    month_income = await session.scalar(
        select(func.coalesce(func.sum(ExpertIncomeRecord.actual_income), 0)).where(
            ExpertIncomeRecord.expert_id == expert.id,
            ExpertIncomeRecord.created_at >= first_day,
        )
    )
    return {
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "total_income": total_income,
        "available_balance": money(expert_user.balance if expert_user else 0),
        "frozen_balance": money(expert_user.frozen_balance if expert_user else 0),
        "month_income": money(month_income),
        "rating": float(expert.rating or 0),
    }


@router.get("/expert/center/orders", response_model=PageOut)
async def expert_center_orders(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    stmt = select(ExpertOrder).where(ExpertOrder.expert_id == expert.id)
    count_stmt = select(func.count(ExpertOrder.id)).where(ExpertOrder.expert_id == expert.id)
    if status:
        stmt = stmt.where(ExpertOrder.status == status)
        count_stmt = count_stmt.where(ExpertOrder.status == status)
    total = await session.scalar(count_stmt)
    result = await session.execute(stmt.order_by(ExpertOrder.id.desc()).offset((page - 1) * page_size).limit(page_size))
    items = []
    for order in result.scalars().all():
        main_order = await session.scalar(select(Order).where(Order.order_type == "expert_service", Order.related_id == order.id))
        items.append(expert_order_item(order, main_order))
    return {"total": total or 0, "page": page, "page_size": page_size, "items": items}


@router.post("/expert/center/orders/{order_id}/accept")
async def accept_expert_order(
        order_id: int,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.expert_id == expert.id))
    if not order:
        raise HTTPException(status_code=404, detail="专家订单不存在")
    if order.status not in ("paid", "processing"):
        raise HTTPException(status_code=400, detail="当前订单状态不可接单")
    order.status = "processing"
    main_order = await session.scalar(select(Order).where(Order.order_type == "expert_service", Order.related_id == order.id))
    if main_order and main_order.status == "paid":
        main_order.status = "processing"
    await session.commit()
    return {"message": "接单成功", "status": order.status}


@router.post("/expert/center/orders/{order_id}/complete")
async def complete_expert_order(
        order_id: int,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.expert_id == expert.id))
    if not order:
        raise HTTPException(status_code=404, detail="专家订单不存在")
    if order.status in ("delivered", "confirmed", "settle_pending", "settled", "completed"):
        raise HTTPException(status_code=400, detail="订单已完成")
    if order.status not in ("paid", "processing"):
        raise HTTPException(status_code=400, detail="当前订单状态不可完成")

    main_order = await session.scalar(select(Order).where(Order.order_type == "expert_service", Order.related_id == order.id))
    if not main_order or main_order.status not in ("paid", "processing"):
        raise HTTPException(status_code=400, detail="主订单未支付，不能完成")
    amount = money(main_order.amount)
    platform_fee = money(order.platform_fee)
    actual_income = money(order.expert_income)
    now = datetime.now()
    order.status = "delivered"
    order.delivered_at = now
    order.settlement_due_at = now + timedelta(days=SETTLEMENT_WAIT_DAYS)
    if main_order:
        main_order.status = "delivered"
        main_order.completed_at = now
    await ensure_pending_income(session, expert, order, main_order)
    await session.commit()
    return {
        "message": "订单已交付",
        "amount": amount,
        "platform_fee": platform_fee,
        "actual_income": actual_income,
    }


@router.post("/expert/center/orders/{order_id}/settle")
async def settle_due_expert_order(
        order_id: int,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.expert_id == expert.id))
    if not order:
        raise HTTPException(status_code=404, detail="专家订单不存在")
    if order.status not in ("delivered", "settle_pending"):
        raise HTTPException(status_code=400, detail="当前订单状态不可结算")
    if order.settlement_due_at and order.settlement_due_at > datetime.now():
        raise HTTPException(status_code=400, detail="订单仍在售后期内，暂不可结算")
    await settle_expert_order(session, expert, order, "鍞悗鏈熸弧鑷姩缁撶畻")
    main_order = await session.scalar(select(Order).where(Order.order_type == "expert_service", Order.related_id == order.id))
    if main_order:
        main_order.status = "settled"
    await session.commit()
    return {"message": "订单已结算", "status": order.status}


@router.get("/expert/center/income", response_model=PageOut)
async def expert_income(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    total = await session.scalar(select(func.count(ExpertIncomeRecord.id)).where(ExpertIncomeRecord.expert_id == expert.id))
    result = await session.execute(
        select(ExpertIncomeRecord)
        .where(ExpertIncomeRecord.expert_id == expert.id)
        .order_by(ExpertIncomeRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {"total": total or 0, "page": page, "page_size": page_size, "items": [income_out(item) for item in result.scalars().all()]}


@router.post("/expert/center/withdrawals", response_model=ExpertWithdrawalOut)
async def create_expert_withdrawal(
        data: ExpertWithdrawalCreateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    expert_user = await session.scalar(select(User).where(User.id == expert.user_id))
    if not expert_user:
        raise HTTPException(status_code=404, detail="专家用户不存在")
    amount = money(data.amount)
    if money(expert_user.balance) < amount:
        raise HTTPException(status_code=400, detail="可提现余额不足")
    expert_user.balance = money(expert_user.balance) - amount
    expert_user.frozen_balance = money(expert_user.frozen_balance) + amount
    withdrawal = ExpertWithdrawal(
        expert_id=expert.id,
        user_id=expert.user_id,
        withdrawal_no=make_withdrawal_no(),
        amount=amount,
        account_name=data.account_name,
        account_no=data.account_no,
        bank_name=data.bank_name,
        status="pending",
    )
    session.add(withdrawal)
    session.add(WalletTransaction(
        user_id=expert.user_id,
        transaction_type="withdraw_freeze",
        amount=-amount,
        balance_after=money(expert_user.balance),
        description=f"涓撳鎻愮幇鐢宠 {withdrawal.withdrawal_no}",
        related_order_id=None,
    ))
    await session.commit()
    await session.refresh(withdrawal)
    return withdrawal_out(withdrawal)


@router.get("/expert/center/withdrawals", response_model=PageOut)
async def list_expert_withdrawals(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    total = await session.scalar(select(func.count(ExpertWithdrawal.id)).where(ExpertWithdrawal.expert_id == expert.id))
    result = await session.execute(
        select(ExpertWithdrawal)
        .where(ExpertWithdrawal.expert_id == expert.id)
        .order_by(ExpertWithdrawal.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {"total": total or 0, "page": page, "page_size": page_size, "items": [withdrawal_out(item) for item in result.scalars().all()]}


@router.get("/expert/center/reviews", response_model=PageOut)
async def list_expert_center_reviews(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    total = await session.scalar(select(func.count(ExpertReview.id)).where(ExpertReview.expert_id == expert.id))
    result = await session.execute(
        select(ExpertReview)
        .where(ExpertReview.expert_id == expert.id)
        .order_by(ExpertReview.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {"total": total or 0, "page": page, "page_size": page_size, "items": [review_to_out(item) for item in result.scalars().all()]}


@router.post("/expert/center/reviews/{review_id}/reply", response_model=ExpertReviewOut)
async def reply_expert_review(
        review_id: int,
        data: ExpertReviewReplyIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    review = await session.scalar(select(ExpertReview).where(ExpertReview.id == review_id, ExpertReview.expert_id == expert.id))
    if not review:
        raise HTTPException(status_code=404, detail="评价不存在")
    review.reply = data.reply
    review.replied_at = datetime.now()
    await session.commit()
    await session.refresh(review)
    return review_to_out(review)


@router.get("/expert/center/after-sales", response_model=PageOut)
async def list_expert_center_after_sales(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        status: str | None = Query(None),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await get_current_expert(user_id, session)
    stmt = select(AfterSaleRequest).where(AfterSaleRequest.expert_id == expert.id)
    count_stmt = select(func.count(AfterSaleRequest.id)).where(AfterSaleRequest.expert_id == expert.id)
    if status:
        stmt = stmt.where(AfterSaleRequest.status == status)
        count_stmt = count_stmt.where(AfterSaleRequest.status == status)
    total = await session.scalar(count_stmt)
    result = await session.execute(stmt.order_by(AfterSaleRequest.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return {"total": total or 0, "page": page, "page_size": page_size, "items": [after_sale_to_out(item) for item in result.scalars().all()]}
