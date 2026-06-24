import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from models.account import ExpertFeeRule, ExpertIncomeRecord, Order, PlatformLedger, WalletTransaction
from models.marketplace import AfterSaleRequest, Expert, ExpertOrder, ExpertReview
from models.user import User
from schemas.marketplace import (
    AfterSaleCreateIn,
    AfterSaleOut,
    ExpertApplyIn,
    ExpertOrderCreateIn,
    ExpertOrderOut,
    ExpertOut,
    ExpertReportIn,
    ExpertReviewCreateIn,
    ExpertReviewOut,
    PageOut,
)

router = APIRouter(tags=["expert"])
auth_handler = AuthHandler()
DEFAULT_PLATFORM_FEE_RATE = Decimal("0.2000")
SETTLEMENT_WAIT_DAYS = 7


def money(value) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def make_order_no() -> str:
    return f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:8].upper()}"


def parse_tags(tags: str):
    return [item for item in tags.split(",") if item]


def expert_to_out(expert: Expert):
    return ExpertOut(
        id=expert.id,
        user_id=expert.user_id,
        name=expert.name,
        avatar=expert.avatar,
        title=expert.title,
        description=expert.description,
        tags=parse_tags(expert.tags),
        price=expert.price,
        experience_years=expert.experience_years,
        status=expert.status,
        rating=expert.rating,
        created_at=expert.created_at,
    )


def order_to_out(order: ExpertOrder, main_order: Order | None = None):
    return ExpertOrderOut(
        id=order.id,
        order_id=main_order.id if main_order else None,
        order_no=main_order.order_no if main_order else None,
        user_id=order.user_id,
        expert_id=order.expert_id,
        name_record_id=order.name_record_id,
        amount=order.amount,
        fee_rate_snapshot=order.fee_rate_snapshot,
        platform_fee=order.platform_fee,
        expert_income=order.expert_income,
        status=order.status,
        report_url=order.report_url,
        report_summary=order.report_summary,
        report_analysis=order.report_analysis,
        report_suggestions=order.report_suggestions,
        delivered_at=order.delivered_at,
        confirmed_at=order.confirmed_at,
        settlement_due_at=order.settlement_due_at,
        settled_at=order.settled_at,
        created_at=order.created_at,
    )


def review_to_out(review: ExpertReview):
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


def after_sale_to_out(item: AfterSaleRequest):
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


async def refresh_expert_rating(session: AsyncSession, expert_id: int):
    avg_rating = await session.scalar(
        select(func.coalesce(func.avg(ExpertReview.rating), 5.0)).where(
            ExpertReview.expert_id == expert_id,
            ExpertReview.status == "visible",
        )
    )
    expert = await session.get(Expert, expert_id)
    if expert:
        expert.rating = round(float(avg_rating or 5.0), 1)


async def get_active_fee_rule(session: AsyncSession) -> ExpertFeeRule | None:
    return await session.scalar(
        select(ExpertFeeRule)
        .where(ExpertFeeRule.status == "active")
        .order_by(ExpertFeeRule.id.desc())
    )


def calculate_fee(amount: Decimal, fee_rate: Decimal) -> tuple[Decimal, Decimal]:
    platform_fee = money(amount * fee_rate)
    return platform_fee, money(amount - platform_fee)


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


async def settle_expert_order(session: AsyncSession, order: ExpertOrder, reason: str = "user confirmed") -> bool:
    if order.status == "settled":
        return False
    if order.status not in ("delivered", "confirmed", "settle_pending"):
        raise HTTPException(status_code=400, detail="当前订单状态不可结算")
    income = await session.scalar(select(ExpertIncomeRecord).where(ExpertIncomeRecord.order_id == order.id))
    if not income:
        raise HTTPException(status_code=400, detail="待结算收入记录不存在")
    if income.status == "settled":
        order.status = "settled"
        order.settled_at = income.settled_at or datetime.now()
        return False
    if income.status != "settle_pending":
        raise HTTPException(status_code=400, detail="收入记录状态不可结算")
    expert = await session.get(Expert, order.expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail="专家不存在")
    expert_user = await session.scalar(select(User).where(User.id == expert.user_id))
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


def make_after_sale_no() -> str:
    return f"AS{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:8].upper()}"


@router.post("/expert/apply", response_model=ExpertOut)
async def apply_expert(
        data: ExpertApplyIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        expert = Expert(
            user_id=int(user_id),
            name=data.name,
            avatar=data.avatar,
            title=data.title,
            description=data.description,
            tags=",".join(data.tags),
            price=data.price,
            experience_years=data.experience_years,
            status="pending",
        )
        session.add(expert)
    return expert_to_out(expert)


@router.get("/experts", response_model=PageOut)
async def list_experts(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        keyword: str | None = Query(None),
        tag: str | None = Query(None),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(Expert).where(Expert.status == "approved")
    count_stmt = select(func.count(Expert.id)).where(Expert.status == "approved")
    if keyword:
        condition = or_(Expert.name.like(f"%{keyword}%"), Expert.title.like(f"%{keyword}%"))
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    if tag:
        stmt = stmt.where(Expert.tags.like(f"%{tag}%"))
        count_stmt = count_stmt.where(Expert.tags.like(f"%{tag}%"))
    total = await session.scalar(count_stmt)
    result = await session.execute(stmt.order_by(Expert.rating.desc()).offset((page - 1) * page_size).limit(page_size))
    return {"total": total or 0, "page": page, "page_size": page_size, "items": [expert_to_out(x) for x in result.scalars().all()]}


@router.get("/experts/{expert_id}", response_model=ExpertOut)
async def expert_detail(expert_id: int, session: AsyncSession = Depends(get_session)):
    expert = await session.scalar(select(Expert).where(Expert.id == expert_id, Expert.status == "approved"))
    if not expert:
        raise HTTPException(status_code=404, detail="专家不存在")
    return expert_to_out(expert)


@router.post("/expert-orders", response_model=ExpertOrderOut)
async def create_expert_order(
        data: ExpertOrderCreateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await session.scalar(select(Expert).where(Expert.id == data.expert_id, Expert.status == "approved"))
    if not expert:
        raise HTTPException(status_code=404, detail="专家不存在或未审核")
    fee_rule = await get_active_fee_rule(session)
    fee_rate = Decimal(str(fee_rule.fee_rate if fee_rule else DEFAULT_PLATFORM_FEE_RATE)).quantize(Decimal("0.0001"))
    amount = money(expert.price)
    platform_fee, expert_income = calculate_fee(amount, fee_rate)
    order = ExpertOrder(
        user_id=int(user_id),
        expert_id=expert.id,
        name_record_id=data.name_record_id,
        amount=amount,
        fee_rule_id=fee_rule.id if fee_rule else None,
        fee_rate_snapshot=fee_rate,
        platform_fee=platform_fee,
        expert_income=expert_income,
        status="pending",
    )
    session.add(order)
    await session.flush()
    main_order = Order(
        user_id=int(user_id),
        order_no=make_order_no(),
        order_type="expert_service",
        amount=amount,
        status="pending",
        related_id=order.id,
    )
    session.add(main_order)
    await session.commit()
    await session.refresh(order)
    await session.refresh(main_order)
    return order_to_out(order, main_order)


@router.get("/expert/orders", response_model=PageOut)
async def expert_orders(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await session.scalar(select(Expert).where(Expert.user_id == int(user_id), Expert.status == "approved"))
    if not expert:
        raise HTTPException(status_code=403, detail="当前用户不是已审核专家")
    stmt = select(ExpertOrder).where(ExpertOrder.expert_id == expert.id)
    total = await session.scalar(select(func.count(ExpertOrder.id)).where(ExpertOrder.expert_id == expert.id))
    result = await session.execute(stmt.order_by(ExpertOrder.id.desc()).offset((page - 1) * page_size).limit(page_size))
    items = []
    for item in result.scalars().all():
        main_order = await session.scalar(select(Order).where(Order.order_type == "expert_service", Order.related_id == item.id))
        items.append(order_to_out(item, main_order))
    return {"total": total or 0, "page": page, "page_size": page_size, "items": items}


@router.post("/expert/orders/{order_id}/report", response_model=ExpertOrderOut)
async def submit_expert_report(
        order_id: int,
        data: ExpertReportIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    expert = await session.scalar(select(Expert).where(Expert.user_id == int(user_id), Expert.status == "approved"))
    if not expert:
        raise HTTPException(status_code=403, detail="当前用户不是已审核专家")
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.expert_id == expert.id))
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status not in ("paid", "processing"):
        raise HTTPException(status_code=400, detail="当前订单状态不可交付")
    main_order = await session.scalar(select(Order).where(Order.order_type == "expert_service", Order.related_id == order.id))
    if not main_order or main_order.status not in ("paid", "processing"):
        raise HTTPException(status_code=400, detail="主订单未支付，不能交付")
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)
    report_path = report_dir / f"expert_order_{order.id}.pdf"
    content = f"专家精批报告\n\n总结：{data.summary}\n\n分析：{data.analysis}\n\n建议：{data.suggestions}\n"
    report_path.write_text(content, encoding="utf-8")
    order.report_summary = data.summary
    order.report_analysis = data.analysis
    order.report_suggestions = data.suggestions
    order.report_url = str(report_path).replace(os.sep, "/")
    now = datetime.now()
    order.status = "delivered"
    order.delivered_at = now
    order.settlement_due_at = now + timedelta(days=SETTLEMENT_WAIT_DAYS)
    main_order = await session.scalar(select(Order).where(Order.order_type == "expert_service", Order.related_id == order.id))
    if main_order:
        main_order.status = "delivered"
        main_order.completed_at = now
    await ensure_pending_income(session, expert, order, main_order)
    await session.commit()
    await session.refresh(order)
    return order_to_out(order, main_order)


@router.post("/expert-orders/{order_id}/confirm", response_model=ExpertOrderOut)
async def confirm_expert_order(
        order_id: int,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.user_id == int(user_id)))
    if not order:
        raise HTTPException(status_code=404, detail="专家订单不存在")
    if order.status not in ("delivered", "settle_pending"):
        raise HTTPException(status_code=400, detail="当前订单状态不可确认")
    main_order = await session.scalar(select(Order).where(Order.order_type == "expert_service", Order.related_id == order.id))
    if not main_order or main_order.status not in ("delivered", "completed"):
        raise HTTPException(status_code=400, detail="主订单状态不可确认")
    order.status = "confirmed"
    order.confirmed_at = datetime.now()
    main_order.status = "confirmed"
    await settle_expert_order(session, order, "鐢ㄦ埛纭涓撳鏈嶅姟")
    main_order.status = "settled"
    await session.commit()
    await session.refresh(order)
    return order_to_out(order, main_order)


@router.get("/expert-orders/{order_id}", response_model=ExpertOrderOut)
async def get_expert_order(
        order_id: int,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.user_id == int(user_id)))
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    main_order = await session.scalar(select(Order).where(Order.order_type == "expert_service", Order.related_id == order.id))
    return order_to_out(order, main_order)


@router.post("/expert-orders/{order_id}/review", response_model=ExpertReviewOut)
async def create_expert_review(
        order_id: int,
        data: ExpertReviewCreateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.user_id == int(user_id)))
    if not order:
        raise HTTPException(status_code=404, detail="专家订单不存在")
    if order.status not in ("settled", "completed"):
        raise HTTPException(status_code=400, detail="订单结算后才能评价")
    exists = await session.scalar(
        select(ExpertReview).where(ExpertReview.expert_order_id == order.id, ExpertReview.user_id == int(user_id))
    )
    if exists:
        raise HTTPException(status_code=400, detail="璇ヨ鍗曞凡璇勪环")
    review = ExpertReview(
        expert_id=order.expert_id,
        expert_order_id=order.id,
        user_id=int(user_id),
        rating=data.rating,
        content=data.content,
        status="visible",
    )
    session.add(review)
    await session.flush()
    await refresh_expert_rating(session, order.expert_id)
    await session.commit()
    await session.refresh(review)
    return review_to_out(review)


@router.get("/experts/{expert_id}/reviews", response_model=PageOut)
async def list_expert_reviews(
        expert_id: int,
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        session: AsyncSession = Depends(get_session),
):
    total = await session.scalar(
        select(func.count(ExpertReview.id)).where(ExpertReview.expert_id == expert_id, ExpertReview.status == "visible")
    )
    result = await session.execute(
        select(ExpertReview)
        .where(ExpertReview.expert_id == expert_id, ExpertReview.status == "visible")
        .order_by(ExpertReview.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {"total": total or 0, "page": page, "page_size": page_size, "items": [review_to_out(item) for item in result.scalars().all()]}


@router.post("/expert-orders/{order_id}/after-sales", response_model=AfterSaleOut)
async def create_after_sale(
        order_id: int,
        data: AfterSaleCreateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.user_id == int(user_id)))
    if not order:
        raise HTTPException(status_code=404, detail="专家订单不存在")
    if order.status not in ("paid", "processing", "delivered", "confirmed", "settle_pending", "settled", "completed"):
        raise HTTPException(status_code=400, detail="褰撳墠璁㈠崟涓嶅彲鐢宠鍞悗")
    main_order = await session.scalar(select(Order).where(Order.order_type == "expert_service", Order.related_id == order.id))
    exists = await session.scalar(
        select(AfterSaleRequest).where(
            AfterSaleRequest.expert_order_id == order.id,
            AfterSaleRequest.status.in_(["pending", "processing"]),
        )
    )
    if exists:
        return after_sale_to_out(exists)
    item = AfterSaleRequest(
        user_id=int(user_id),
        expert_id=order.expert_id,
        expert_order_id=order.id,
        order_id=main_order.id if main_order else None,
        request_no=make_after_sale_no(),
        request_type=data.request_type,
        reason=data.reason,
        description=data.description,
        status="pending",
    )
    session.add(item)
    order.status = "after_sale"
    if main_order:
        main_order.status = "after_sale"
    await session.commit()
    await session.refresh(item)
    return after_sale_to_out(item)


@router.get("/expert-orders/{order_id}/after-sales", response_model=PageOut)
async def list_order_after_sales(
        order_id: int,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.user_id == int(user_id)))
    if not order:
        raise HTTPException(status_code=404, detail="专家订单不存在")
    result = await session.execute(
        select(AfterSaleRequest).where(AfterSaleRequest.expert_order_id == order.id).order_by(AfterSaleRequest.id.desc())
    )
    items = [after_sale_to_out(item) for item in result.scalars().all()]
    return {"total": len(items), "page": 1, "page_size": len(items), "items": items}
