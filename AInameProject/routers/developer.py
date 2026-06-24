from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from models.developer import DeveloperSubscription, Plan
from repository.developer_repo import DeveloperRepository
from schemas.developer import (
    ApiKeyCreateIn,
    ApiKeyCreateOut,
    ApiKeyOut,
    DeveloperApplyIn,
    DeveloperDashboardOut,
    DeveloperOut,
    PageOut,
    PlanOut,
    SubscriptionCreateIn,
    DeveloperSubscriptionOut,
    UsageLogOut,
)

router = APIRouter(prefix="/developer", tags=["developer"])
auth_handler = AuthHandler()


async def get_current_developer(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = DeveloperRepository(session)
    developer = await repo.get_by_user_id(int(user_id))
    if not developer:
        raise HTTPException(status_code=404, detail="请先申请成为开发者")
    if developer.status != "approved":
        raise HTTPException(status_code=403, detail="开发者账号尚未审核通过")
    return developer


@router.post("/apply", response_model=DeveloperOut)
async def apply_developer(
    data: DeveloperApplyIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = DeveloperRepository(session)
    async with session.begin():
        developer = await repo.apply(int(user_id), data)
    return DeveloperOut.model_validate(developer, from_attributes=True)


@router.get("/profile", response_model=DeveloperOut)
async def developer_profile(developer=Depends(get_current_developer)):
    return DeveloperOut.model_validate(developer, from_attributes=True)


@router.get("/dashboard", response_model=DeveloperDashboardOut)
async def developer_dashboard(
    developer=Depends(get_current_developer),
    session: AsyncSession = Depends(get_session),
):
    repo = DeveloperRepository(session)
    return await repo.dashboard(developer.id)


@router.get("/plans", response_model=PageOut)
async def developer_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    developer=Depends(get_current_developer),
    session: AsyncSession = Depends(get_session),
):
    total = await session.scalar(select(func.count(Plan.id)).where(Plan.status == "active")) or 0
    result = await session.execute(
        select(Plan)
        .where(Plan.status == "active")
        .order_by(Plan.price.asc(), Plan.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [PlanOut.model_validate(item, from_attributes=True) for item in result.scalars().all()]
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.post("/subscription", response_model=DeveloperSubscriptionOut)
async def subscribe_plan(
    data: SubscriptionCreateIn,
    developer=Depends(get_current_developer),
    session: AsyncSession = Depends(get_session),
):
    plan = await session.get(Plan, data.plan_id)
    if not plan or plan.status != "active":
        raise HTTPException(status_code=404, detail="套餐不存在或已禁用")
    now = datetime.now()
    base_time = developer.subscription_expires_at if developer.subscription_expires_at and developer.subscription_expires_at > now else now
    expires_at = base_time + timedelta(days=30 * data.months)
    subscription = DeveloperSubscription(
        developer_id=developer.id,
        plan_id=plan.id,
        status="active",
        started_at=now,
        expires_at=expires_at,
    )
    developer.plan_id = plan.id
    developer.subscription_status = "active"
    developer.subscription_expires_at = expires_at
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return DeveloperSubscriptionOut.model_validate(subscription, from_attributes=True)


@router.post("/api-keys", response_model=ApiKeyCreateOut)
async def create_api_key(
    data: ApiKeyCreateIn,
    developer=Depends(get_current_developer),
    session: AsyncSession = Depends(get_session),
):
    repo = DeveloperRepository(session)
    row, api_key, secret_key = await repo.create_api_key(developer.id, data)
    await session.commit()
    await session.refresh(row)
    return ApiKeyCreateOut(id=row.id, name=row.name, api_key=api_key, secret_key=secret_key, quota=row.quota)


@router.get("/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(
    developer=Depends(get_current_developer),
    session: AsyncSession = Depends(get_session),
):
    repo = DeveloperRepository(session)
    keys = await repo.list_api_keys(developer.id)
    return [ApiKeyOut.model_validate(item, from_attributes=True) for item in keys]


@router.put("/api-keys/{key_id}/disable", response_model=ApiKeyOut)
async def disable_api_key(
    key_id: int,
    developer=Depends(get_current_developer),
    session: AsyncSession = Depends(get_session),
):
    repo = DeveloperRepository(session)
    key = await repo.disable_api_key(developer.id, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    await session.commit()
    await session.refresh(key)
    return ApiKeyOut.model_validate(key, from_attributes=True)


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    developer=Depends(get_current_developer),
    session: AsyncSession = Depends(get_session),
):
    repo = DeveloperRepository(session)
    deleted = await repo.delete_api_key(developer.id, key_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    await session.commit()
    return {"message": "API Key 已删除"}


@router.get("/logs", response_model=PageOut)
async def developer_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    developer=Depends(get_current_developer),
    session: AsyncSession = Depends(get_session),
):
    repo = DeveloperRepository(session)
    total, items = await repo.usage_logs(developer.id, page, page_size)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [UsageLogOut.model_validate(item) for item in items],
    }
