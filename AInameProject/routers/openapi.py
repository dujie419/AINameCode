import hashlib
import hmac
from datetime import datetime, timedelta
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_deepseek import ChatDeepSeek
from pydantic import BaseModel, SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from core.api_key import decrypt_secret
from dependencies import get_session
from models.developer import ApiBillingSummary, ApiKey, ApiRateLimitRule, ApiUsageLog, BillingRecord, Developer, Plan
from repository.developer_repo import get_active_api_key
from schemas.developer import (
    BabyNameIn,
    CompanyNameIn,
    LocationNameIn,
    NovelCharacterIn,
    NpcNameIn,
    OpenApiCredential,
    OpenNameOut,
)

router = APIRouter(prefix="/openapi", tags=["openapi"])
security = HTTPBearer()


class OpenNameModel(BaseModel):
    name: str
    meaning: str = ""


llm = ChatDeepSeek(
    model=settings.DEEPSEEK_MODEL,
    api_key=SecretStr(settings.DEEPSEEK_API_KEY),
    temperature=0.7,
)
structured_llm = llm.with_structured_output(OpenNameModel).with_retry(stop_after_attempt=3)


async def get_openapi_credential(
    request: Request,
    auth: HTTPAuthorizationCredentials = Security(security),
    session: AsyncSession = Depends(get_session),
) -> OpenApiCredential:
    key = await get_active_api_key(session, auth.credentials)
    if not key:
        raise HTTPException(status_code=401, detail="API Key 无效或已禁用")
    timestamp = request.headers.get("x-api-timestamp")
    signature = request.headers.get("x-api-signature")
    if not timestamp or not signature:
        raise HTTPException(status_code=401, detail="缺少 API 签名")
    try:
        timestamp_value = int(timestamp)
    except ValueError:
        raise HTTPException(status_code=401, detail="API 签名时间戳无效")
    if abs(int(datetime.now().timestamp()) - timestamp_value) > 300:
        raise HTTPException(status_code=401, detail="API 签名已过期")
    body = (await request.body()).decode("utf-8")
    payload = f"{timestamp}.{request.method.upper()}.{request.url.path}.{body}"
    secret = decrypt_secret(key.secret_key_encrypted)
    expected = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="API 签名校验失败")
    developer = await session.get(Developer, key.developer_id)
    if not developer or developer.status != "approved":
        raise HTTPException(status_code=403, detail="开发者账号尚未审核通过")
    if developer.subscription_status != "active":
        raise HTTPException(status_code=402, detail="开发者套餐未开通")
    if developer.subscription_expires_at and developer.subscription_expires_at < datetime.now():
        developer.subscription_status = "expired"
        await session.commit()
        raise HTTPException(status_code=402, detail="开发者套餐已过期")

    plan = await session.get(Plan, developer.plan_id) if developer.plan_id else None
    qpm_limit = plan.qpm_limit if plan else 60
    daily_quota = plan.daily_quota if plan else 0
    monthly_quota = plan.quota if plan else key.quota
    token_price = plan.token_price if plan else 0.0001

    rule = await session.scalar(
        select(ApiRateLimitRule)
        .where(
            ApiRateLimitRule.status == "active",
            (ApiRateLimitRule.api_key_id == key.id) | (ApiRateLimitRule.developer_id == key.developer_id),
        )
        .order_by(ApiRateLimitRule.api_key_id.desc())
    )
    if rule:
        qpm_limit = rule.qpm_limit or qpm_limit
        daily_quota = rule.daily_quota or daily_quota
        monthly_quota = rule.monthly_quota or monthly_quota

    if key.used_quota >= key.quota:
        raise HTTPException(status_code=429, detail="API Key 额度已用完")

    now = datetime.now()
    minute_calls = await session.scalar(
        select(func.count(ApiUsageLog.id)).where(ApiUsageLog.api_key_id == key.id, ApiUsageLog.created_at >= now - timedelta(minutes=1))
    ) or 0
    if qpm_limit and minute_calls >= qpm_limit:
        raise HTTPException(status_code=429, detail="API 调用过于频繁，请稍后再试")

    today_calls = await session.scalar(
        select(func.count(ApiUsageLog.id)).where(ApiUsageLog.api_key_id == key.id, func.date(ApiUsageLog.created_at) == now.date())
    ) or 0
    if daily_quota and today_calls >= daily_quota:
        raise HTTPException(status_code=429, detail="今日 API 调用额度已用完")

    month_calls = await session.scalar(
        select(func.count(ApiUsageLog.id)).where(
            ApiUsageLog.api_key_id == key.id,
            func.extract("year", ApiUsageLog.created_at) == now.year,
            func.extract("month", ApiUsageLog.created_at) == now.month,
        )
    ) or 0
    if monthly_quota and month_calls >= monthly_quota:
        raise HTTPException(status_code=429, detail="本月 API 调用额度已用完")

    return OpenApiCredential(
        developer_id=key.developer_id,
        api_key_id=key.id,
        plan_id=developer.plan_id,
        qpm_limit=qpm_limit,
        daily_quota=daily_quota,
        monthly_quota=monthly_quota,
        token_price=token_price,
    )


def estimate_tokens(prompt: str, result: OpenNameModel) -> int:
    return max(1, len(prompt + result.name + result.meaning) // 2)


async def generate_open_name(prompt: str) -> tuple[OpenNameModel, int]:
    result = await structured_llm.ainvoke(prompt)
    tokens = estimate_tokens(prompt, result)
    return result, tokens


async def record_usage(
    session: AsyncSession,
    credential: OpenApiCredential,
    endpoint: str,
    tokens: int,
    request_time: datetime,
    response_time: int,
    request_ip: str | None,
    status_code: int = 200,
):
    log = ApiUsageLog(
        developer_id=credential.developer_id,
        api_key_id=credential.api_key_id,
        endpoint=endpoint,
        tokens=tokens,
        request_time=request_time,
        response_time=response_time,
        request_ip=request_ip,
        status_code=status_code,
    )
    cost = round(tokens * credential.token_price, 4)
    bill = BillingRecord(
        developer_id=credential.developer_id,
        api_key_id=credential.api_key_id,
        usage_tokens=tokens,
        cost=cost,
    )
    key = await session.get(ApiKey, credential.api_key_id)
    if key and status_code < 400:
        key.used_quota += 1
    session.add(log)
    session.add(bill)
    period = request_time.strftime("%Y-%m")
    summary = await session.scalar(
        select(ApiBillingSummary).where(
            ApiBillingSummary.developer_id == credential.developer_id,
            ApiBillingSummary.period == period,
            ApiBillingSummary.status == "open",
        )
    )
    if not summary:
        summary = ApiBillingSummary(
            developer_id=credential.developer_id,
            period=period,
            total_calls=0,
            total_tokens=0,
            total_cost=0,
            status="open",
        )
        session.add(summary)
    if status_code < 400:
        summary.total_calls += 1
        summary.total_tokens += tokens
        summary.total_cost = round(float(summary.total_cost or 0) + cost, 4)


async def run_endpoint(
    request: Request,
    session: AsyncSession,
    credential: OpenApiCredential,
    endpoint: str,
    prompt: str,
) -> OpenNameOut:
    start = perf_counter()
    request_time = datetime.now()
    status_code = 200
    tokens = 0
    try:
        result, tokens = await generate_open_name(prompt)
        return OpenNameOut(name=result.name, meaning=result.meaning, tokens=tokens)
    except Exception:
        status_code = 500
        raise
    finally:
        response_time = int((perf_counter() - start) * 1000)
        await record_usage(
            session=session,
            credential=credential,
            endpoint=endpoint,
            tokens=tokens,
            request_time=request_time,
            response_time=response_time,
            request_ip=request.client.host if request.client else None,
            status_code=status_code,
        )
        await session.commit()


@router.post("/npc-name", response_model=OpenNameOut)
async def npc_name(
    data: NpcNameIn,
    request: Request,
    credential: OpenApiCredential = Depends(get_openapi_credential),
    session: AsyncSession = Depends(get_session),
):
    prompt = f"为游戏NPC生成一个中文名字。种族:{data.race}; 性别:{data.gender}; 风格:{data.style}。返回名字和简短寓意。"
    return await run_endpoint(request, session, credential, "/openapi/npc-name", prompt)


@router.post("/novel-character", response_model=OpenNameOut)
async def novel_character(
    data: NovelCharacterIn,
    request: Request,
    credential: OpenApiCredential = Depends(get_openapi_credential),
    session: AsyncSession = Depends(get_session),
):
    prompt = f"为小说角色生成一个中文名字。小说类型:{data.novel_type}; 性别:{data.gender}。返回名字和简短寓意。"
    return await run_endpoint(request, session, credential, "/openapi/novel-character", prompt)


@router.post("/location-name", response_model=OpenNameOut)
async def location_name(
    data: LocationNameIn,
    request: Request,
    credential: OpenApiCredential = Depends(get_openapi_credential),
    session: AsyncSession = Depends(get_session),
):
    prompt = f"生成一个中文地名或组织名，风格:{data.style}。返回名字和简短寓意。"
    return await run_endpoint(request, session, credential, "/openapi/location-name", prompt)


@router.post("/baby-name", response_model=OpenNameOut)
async def baby_name(
    data: BabyNameIn,
    request: Request,
    credential: OpenApiCredential = Depends(get_openapi_credential),
    session: AsyncSession = Depends(get_session),
):
    prompt = f"为宝宝起一个中文姓名。姓氏:{data.surname}; 性别:{data.gender}。返回名字和简短寓意。"
    return await run_endpoint(request, session, credential, "/openapi/baby-name", prompt)


@router.post("/company-name", response_model=OpenNameOut)
async def company_name(
    data: CompanyNameIn,
    request: Request,
    credential: OpenApiCredential = Depends(get_openapi_credential),
    session: AsyncSession = Depends(get_session),
):
    prompt = f"为企业品牌生成一个中文公司名。行业:{data.industry}; 风格:{data.style}。返回名字和简短寓意。"
    return await run_endpoint(request, session, credential, "/openapi/company-name", prompt)
