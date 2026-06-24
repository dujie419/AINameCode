from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_key import encrypt_secret, generate_api_key, generate_secret_key, hash_token
from models.developer import ApiKey, ApiUsageLog, BillingRecord, Developer, Plan
from models.user import User
from schemas.developer import ApiKeyCreateIn, DeveloperApplyIn


class DeveloperRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> Developer | None:
        return await self.session.scalar(select(Developer).where(Developer.user_id == user_id))

    async def apply(self, user_id: int, data: DeveloperApplyIn) -> Developer:
        user = await self.session.scalar(select(User).where(User.id == user_id))
        developer = await self.get_by_user_id(user_id)
        if developer:
            developer.company_name = data.company_name
            developer.contact_name = data.contact_name
            developer.status = "pending"
            return developer

        developer = Developer(
            user_id=user_id,
            company_name=data.company_name,
            contact_name=data.contact_name,
            email=user.email if user else "",
            status="pending",
        )
        self.session.add(developer)
        return developer

    async def list_api_keys(self, developer_id: int) -> list[ApiKey]:
        result = await self.session.execute(
            select(ApiKey).where(ApiKey.developer_id == developer_id).order_by(ApiKey.id.desc())
        )
        return list(result.scalars().all())

    async def create_api_key(self, developer_id: int, data: ApiKeyCreateIn) -> tuple[ApiKey, str, str]:
        developer = await self.session.get(Developer, developer_id)
        quota = data.quota
        if developer and developer.plan_id:
            plan = await self.session.get(Plan, developer.plan_id)
            if plan and plan.quota > 0:
                quota = min(quota, plan.quota)
        api_key = generate_api_key()
        secret_key = generate_secret_key()
        row = ApiKey(
            developer_id=developer_id,
            name=data.name,
            api_key_prefix=api_key.prefix,
            api_key_hash=api_key.digest,
            secret_key_prefix=secret_key.prefix,
            secret_key_encrypted=encrypt_secret(secret_key.plain),
            secret_key_hash=secret_key.digest,
            quota=quota,
        )
        self.session.add(row)
        return row, api_key.plain, secret_key.plain

    async def disable_api_key(self, developer_id: int, key_id: int) -> ApiKey | None:
        key = await self.session.scalar(
            select(ApiKey).where(ApiKey.id == key_id, ApiKey.developer_id == developer_id)
        )
        if key:
            key.status = "disabled"
        return key

    async def delete_api_key(self, developer_id: int, key_id: int) -> bool:
        key = await self.session.scalar(
            select(ApiKey).where(ApiKey.id == key_id, ApiKey.developer_id == developer_id)
        )
        if not key:
            return False
        await self.session.delete(key)
        return True

    async def dashboard(self, developer_id: int) -> dict:
        developer = await self.session.get(Developer, developer_id)
        plan = await self.session.get(Plan, developer.plan_id) if developer and developer.plan_id else None
        api_key_count = await self.session.scalar(
            select(func.count(ApiKey.id)).where(ApiKey.developer_id == developer_id)
        ) or 0
        today_calls = await self.session.scalar(
            select(func.count(ApiUsageLog.id)).where(
                ApiUsageLog.developer_id == developer_id,
                func.date(ApiUsageLog.created_at) == date.today(),
            )
        ) or 0
        total_calls = await self.session.scalar(
            select(func.count(ApiUsageLog.id)).where(ApiUsageLog.developer_id == developer_id)
        ) or 0
        total_tokens = await self.session.scalar(
            select(func.coalesce(func.sum(ApiUsageLog.tokens), 0)).where(ApiUsageLog.developer_id == developer_id)
        ) or 0
        month_cost = await self.session.scalar(
            select(func.coalesce(func.sum(BillingRecord.cost), 0)).where(
                BillingRecord.developer_id == developer_id,
                func.extract("year", BillingRecord.created_at) == date.today().year,
                func.extract("month", BillingRecord.created_at) == date.today().month,
            )
        ) or 0
        today_quota_used = today_calls
        month_quota_used = total_calls
        today_limit = plan.daily_quota if plan else 0
        month_limit = plan.quota if plan else 0
        return {
            "api_key_count": api_key_count,
            "today_calls": today_calls,
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "month_cost": float(month_cost),
            "plan_name": plan.name if plan else None,
            "plan_quota": plan.quota if plan else 0,
            "plan_daily_quota": plan.daily_quota if plan else 0,
            "plan_qpm_limit": plan.qpm_limit if plan else 60,
            "token_price": plan.token_price if plan else 0.0001,
            "subscription_status": developer.subscription_status if developer else None,
            "subscription_expires_at": developer.subscription_expires_at if developer else None,
            "today_quota_used": today_quota_used,
            "month_quota_used": month_quota_used,
            "today_quota_remaining": max(today_limit - today_quota_used, 0) if today_limit else None,
            "month_quota_remaining": max(month_limit - month_quota_used, 0) if month_limit else None,
        }

    async def usage_logs(self, developer_id: int, page: int, page_size: int) -> tuple[int, list[dict]]:
        total = await self.session.scalar(
            select(func.count(ApiUsageLog.id)).where(ApiUsageLog.developer_id == developer_id)
        ) or 0
        result = await self.session.execute(
            select(ApiUsageLog)
            .where(ApiUsageLog.developer_id == developer_id)
            .order_by(ApiUsageLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        developer = await self.session.get(Developer, developer_id)
        plan = await self.session.get(Plan, developer.plan_id) if developer and developer.plan_id else None
        token_price = plan.token_price if plan else 0.0001
        logs = []
        for item in result.scalars().all():
            logs.append({
                "id": item.id,
                "endpoint": item.endpoint,
                "tokens": item.tokens,
                "response_time": item.response_time,
                "request_ip": item.request_ip,
                "status_code": item.status_code,
                "cost": round(float(item.tokens or 0) * float(token_price), 4) if item.status_code < 400 else 0,
                "created_at": item.created_at,
            })
        return total, logs


async def get_active_api_key(session: AsyncSession, bearer_token: str) -> ApiKey | None:
    return await session.scalar(
        select(ApiKey).where(ApiKey.api_key_hash == hash_token(bearer_token), ApiKey.status == "active")
    )
