from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin_auth import get_current_admin
from dependencies import get_session
from models.developer import (
    ApiBillingSummary,
    ApiKey,
    ApiRateLimitRule,
    ApiReconciliationRecord,
    ApiUsageLog,
    BillingRecord,
    Developer,
    DeveloperSubscription,
    Plan,
)
from schemas.admin import AdminTokenData, PageOut
from schemas.developer import (
    ApiKeyOut,
    ApiReconciliationOut,
    BillingSummaryOut,
    DeveloperOut,
    DeveloperSubscriptionOut,
    PlanIn,
    PlanOut,
    RateLimitRuleIn,
    RateLimitRuleOut,
    SubscriptionCreateIn,
    UsageLogOut,
)

router = APIRouter(prefix="/admin", tags=["admin-open-platform"])


def plan_out(item: Plan) -> PlanOut:
    return PlanOut.model_validate(item, from_attributes=True)


@router.get("/developers", response_model=PageOut)
async def admin_developers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = Query(None),
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Developer)
    count_stmt = select(func.count(Developer.id))
    if status:
        stmt = stmt.where(Developer.status == status)
        count_stmt = count_stmt.where(Developer.status == status)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(
        stmt.order_by(Developer.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [DeveloperOut.model_validate(item, from_attributes=True) for item in result.scalars().all()],
    }


@router.put("/developers/{developer_id}/approve", response_model=DeveloperOut)
async def approve_developer(
    developer_id: int,
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    developer = await session.get(Developer, developer_id)
    if not developer:
        raise HTTPException(status_code=404, detail="开发者不存在")
    developer.status = "approved"
    if not developer.plan_id:
        free_plan = await session.scalar(select(Plan).where(Plan.status == "active").order_by(Plan.price.asc(), Plan.id.asc()))
        if free_plan:
            now = datetime.now()
            expires_at = now + timedelta(days=30)
            developer.plan_id = free_plan.id
            developer.subscription_status = "active"
            developer.subscription_expires_at = expires_at
            session.add(DeveloperSubscription(
                developer_id=developer.id,
                plan_id=free_plan.id,
                status="active",
                started_at=now,
                expires_at=expires_at,
            ))
    await session.commit()
    await session.refresh(developer)
    return DeveloperOut.model_validate(developer, from_attributes=True)


@router.put("/developers/{developer_id}/reject", response_model=DeveloperOut)
async def reject_developer(
    developer_id: int,
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    developer = await session.get(Developer, developer_id)
    if not developer:
        raise HTTPException(status_code=404, detail="开发者不存在")
    developer.status = "rejected"
    await session.commit()
    await session.refresh(developer)
    return DeveloperOut.model_validate(developer, from_attributes=True)


@router.get("/api-keys", response_model=PageOut)
async def admin_api_keys(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    developer_id: int | None = Query(None),
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(ApiKey)
    count_stmt = select(func.count(ApiKey.id))
    if developer_id:
        stmt = stmt.where(ApiKey.developer_id == developer_id)
        count_stmt = count_stmt.where(ApiKey.developer_id == developer_id)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(stmt.order_by(ApiKey.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [ApiKeyOut.model_validate(item, from_attributes=True) for item in result.scalars().all()],
    }


@router.get("/api-usage-logs", response_model=PageOut)
async def admin_api_usage_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    developer_id: int | None = Query(None),
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(ApiUsageLog)
    count_stmt = select(func.count(ApiUsageLog.id))
    if developer_id:
        stmt = stmt.where(ApiUsageLog.developer_id == developer_id)
        count_stmt = count_stmt.where(ApiUsageLog.developer_id == developer_id)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(stmt.order_by(ApiUsageLog.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [UsageLogOut.model_validate(item, from_attributes=True) for item in result.scalars().all()],
    }


@router.get("/billing-records", response_model=PageOut)
async def admin_billing_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    developer_id: int | None = Query(None),
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(BillingRecord)
    count_stmt = select(func.count(BillingRecord.id))
    if developer_id:
        stmt = stmt.where(BillingRecord.developer_id == developer_id)
        count_stmt = count_stmt.where(BillingRecord.developer_id == developer_id)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(stmt.order_by(BillingRecord.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return {"total": total, "page": page, "page_size": page_size, "items": [item.__dict__ for item in result.scalars().all()]}


@router.get("/plans", response_model=PageOut)
async def admin_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    total = await session.scalar(select(func.count(Plan.id))) or 0
    result = await session.execute(select(Plan).order_by(Plan.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return {"total": total, "page": page, "page_size": page_size, "items": [plan_out(item) for item in result.scalars().all()]}


@router.post("/plans", response_model=PlanOut)
async def create_plan(
    data: PlanIn,
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    plan = Plan(**data.model_dump())
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan_out(plan)


@router.put("/plans/{plan_id}", response_model=PlanOut)
async def update_plan(
    plan_id: int,
    data: PlanIn,
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    plan = await session.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")
    for key, value in data.model_dump().items():
        setattr(plan, key, value)
    await session.commit()
    await session.refresh(plan)
    return plan_out(plan)


@router.post("/developers/{developer_id}/subscription", response_model=DeveloperSubscriptionOut)
async def subscribe_developer_plan(
    developer_id: int,
    data: SubscriptionCreateIn,
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    developer = await session.get(Developer, developer_id)
    plan = await session.get(Plan, data.plan_id)
    if not developer:
        raise HTTPException(status_code=404, detail="开发者不存在")
    if not plan or plan.status != "active":
        raise HTTPException(status_code=404, detail="套餐不存在或已禁用")
    now = datetime.now()
    expires_at = now + timedelta(days=30 * data.months)
    sub = DeveloperSubscription(
        developer_id=developer.id,
        plan_id=plan.id,
        status="active",
        started_at=now,
        expires_at=expires_at,
    )
    developer.plan_id = plan.id
    developer.subscription_status = "active"
    developer.subscription_expires_at = expires_at
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return DeveloperSubscriptionOut.model_validate(sub, from_attributes=True)


@router.get("/subscriptions", response_model=PageOut)
async def admin_subscriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    developer_id: int | None = Query(None),
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(DeveloperSubscription)
    count_stmt = select(func.count(DeveloperSubscription.id))
    if developer_id:
        stmt = stmt.where(DeveloperSubscription.developer_id == developer_id)
        count_stmt = count_stmt.where(DeveloperSubscription.developer_id == developer_id)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(stmt.order_by(DeveloperSubscription.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return {"total": total, "page": page, "page_size": page_size, "items": [DeveloperSubscriptionOut.model_validate(item, from_attributes=True) for item in result.scalars().all()]}


@router.post("/rate-limit-rules", response_model=RateLimitRuleOut)
async def create_rate_limit_rule(
    data: RateLimitRuleIn,
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    rule = ApiRateLimitRule(**data.model_dump())
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return RateLimitRuleOut.model_validate(rule, from_attributes=True)


@router.get("/rate-limit-rules", response_model=PageOut)
async def list_rate_limit_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    developer_id: int | None = Query(None),
    api_key_id: int | None = Query(None),
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(ApiRateLimitRule)
    count_stmt = select(func.count(ApiRateLimitRule.id))
    if developer_id:
        stmt = stmt.where(ApiRateLimitRule.developer_id == developer_id)
        count_stmt = count_stmt.where(ApiRateLimitRule.developer_id == developer_id)
    if api_key_id:
        stmt = stmt.where(ApiRateLimitRule.api_key_id == api_key_id)
        count_stmt = count_stmt.where(ApiRateLimitRule.api_key_id == api_key_id)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(stmt.order_by(ApiRateLimitRule.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return {"total": total, "page": page, "page_size": page_size, "items": [RateLimitRuleOut.model_validate(item, from_attributes=True) for item in result.scalars().all()]}


@router.get("/billing-summaries", response_model=PageOut)
async def admin_billing_summaries(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    developer_id: int | None = Query(None),
    period: str | None = Query(None),
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(ApiBillingSummary)
    count_stmt = select(func.count(ApiBillingSummary.id))
    if developer_id:
        stmt = stmt.where(ApiBillingSummary.developer_id == developer_id)
        count_stmt = count_stmt.where(ApiBillingSummary.developer_id == developer_id)
    if period:
        stmt = stmt.where(ApiBillingSummary.period == period)
        count_stmt = count_stmt.where(ApiBillingSummary.period == period)
    total = await session.scalar(count_stmt) or 0
    result = await session.execute(stmt.order_by(ApiBillingSummary.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return {"total": total, "page": page, "page_size": page_size, "items": [BillingSummaryOut.model_validate(item, from_attributes=True) for item in result.scalars().all()]}


@router.post("/api-reconciliations", response_model=ApiReconciliationOut)
async def create_api_reconciliation(
    period: str = Query(...),
    developer_id: int | None = Query(None),
    admin: AdminTokenData = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    usage_stmt = select(
        func.count(ApiUsageLog.id),
        func.coalesce(func.sum(ApiUsageLog.tokens), 0),
    ).where(func.date_format(ApiUsageLog.created_at, "%Y-%m") == period)
    billing_stmt = select(
        func.count(BillingRecord.id),
        func.coalesce(func.sum(BillingRecord.usage_tokens), 0),
    ).where(func.date_format(BillingRecord.created_at, "%Y-%m") == period)
    if developer_id:
        usage_stmt = usage_stmt.where(ApiUsageLog.developer_id == developer_id)
        billing_stmt = billing_stmt.where(BillingRecord.developer_id == developer_id)
    usage_count, usage_tokens = (await session.execute(usage_stmt)).one()
    billing_count, billed_tokens = (await session.execute(billing_stmt)).one()
    status = "matched" if int(usage_count or 0) == int(billing_count or 0) and int(usage_tokens or 0) == int(billed_tokens or 0) else "mismatch"
    record = ApiReconciliationRecord(
        period=period,
        developer_id=developer_id,
        usage_log_count=usage_count or 0,
        billing_record_count=billing_count or 0,
        usage_tokens=usage_tokens or 0,
        billed_tokens=billed_tokens or 0,
        status=status,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return ApiReconciliationOut.model_validate(record, from_attributes=True)
