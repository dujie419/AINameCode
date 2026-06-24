import json

from sqlalchemy import select
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from models.brand_visual import BrandVisualRecord
from schemas.brand_visual import (
    BrandLogoImageIn,
    BrandLogoImageOut,
    BrandVisualGenerateIn,
    BrandVisualGenerateOut,
    BusinessCardCopy,
)
from services.bailian_service import BailianService
from services.quota_service import ensure_quota_available, record_usage

router = APIRouter(prefix="/brand/visual", tags=["brand_visual"])
auth_handler = AuthHandler()


def normalize_color_palette(color_palette):
    if not isinstance(color_palette, list):
        return []
    normalized = []
    for item in color_palette:
        if isinstance(item, str):
            normalized.append(item)
        elif isinstance(item, dict):
            name = item.get("name") or item.get("color") or item.get("label") or ""
            hex_value = item.get("hex") or item.get("value") or item.get("code") or ""
            text = " ".join([str(value) for value in [name, hex_value] if value])
            normalized.append(text or json.dumps(item, ensure_ascii=False))
        else:
            normalized.append(str(item))
    return normalized


@router.post("/generate", response_model=BrandVisualGenerateOut)
async def generate_brand_visual(
        data: BrandVisualGenerateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    if data.mode == "card":
        await ensure_quota_available(user_id, "business_card", session)

    service = BailianService()
    result = await service.generate_brand_visual(data)
    visual_prompt = result.get("logo_prompt") or result.get("card_image_prompt", "")

    business_card_copy = BusinessCardCopy(
        company_name=data.name,
        slogan=result.get("slogan", ""),
        layout=result.get("business_card_layout", ""),
        person_name=result.get("person_name", data.name if data.mode == "card" else ""),
        title=result.get("title", ""),
        contact_placeholders=result.get("contact_placeholders", []),
        front_layout=result.get("front_layout", ""),
        back_layout=result.get("back_layout", ""),
        image_prompt=result.get("card_image_prompt", visual_prompt),
    )
    out = BrandVisualGenerateOut(
        id=None,
        mode=data.mode,
        name=data.name,
        slogan=result.get("slogan", ""),
        logo_concept=result.get("logo_concept", ""),
        logo_prompt=visual_prompt,
        color_palette=normalize_color_palette(result.get("color_palette", [])),
        typography_style=result.get("typography_style", ""),
        business_card_layout=result.get("business_card_layout", ""),
        business_card_copy=business_card_copy,
        brand_story=result.get("brand_story", ""),
        marketing_copy=result.get("marketing_copy", ""),
        brand_visual_report=result.get("brand_visual_report", ""),
        image_url=None,
    )

    record = BrandVisualRecord(
        user_id=int(user_id),
        mode=data.mode,
        name=data.name,
        industry=data.industry,
        style=data.style,
        meaning=data.meaning,
        slogan=out.slogan,
        logo_prompt=out.logo_prompt,
        brand_report=json.dumps(out.model_dump(mode="json"), ensure_ascii=False),
        image_url=out.image_url,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    out.id = record.id
    out.created_at = record.created_at
    if data.mode == "card":
        await record_usage(user_id, "business_card", session, reason="名片方案生成", related_id=record.id)
    return out


@router.post("/image", response_model=BrandLogoImageOut)
async def generate_brand_logo_image(
        data: BrandLogoImageIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    await ensure_quota_available(user_id, "image_generate", session)
    service = BailianService()
    result = await service.generate_image(logo_prompt=data.logo_prompt, size=data.size, n=data.n)
    image_url = result.get("image_url")
    if data.record_id and image_url:
        record = await session.scalar(
            select(BrandVisualRecord).where(
                BrandVisualRecord.id == data.record_id,
                BrandVisualRecord.user_id == int(user_id),
            )
        )
        if record:
            record.image_url = image_url
            await session.commit()
    if image_url:
        await record_usage(user_id, "image_generate", session, reason="图片生成", related_id=data.record_id)
    return result
