from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class BrandVisualGenerateIn(BaseModel):
    mode: Literal["brand", "card"] = "brand"
    name: Annotated[str, Field(..., min_length=1, max_length=100)]
    industry: Annotated[str, Field("", max_length=100)]
    style: Annotated[str, Field("", max_length=200)]
    meaning: str = ""
    target_users: str = ""
    usage_scene: str = ""
    name_record_id: int | None = None


class BusinessCardCopy(BaseModel):
    company_name: str
    slogan: str
    layout: str
    person_name: str = ""
    title: str = ""
    contact_placeholders: list[str] = Field(default_factory=list)
    front_layout: str = ""
    back_layout: str = ""
    image_prompt: str = ""


class BrandVisualGenerateOut(BaseModel):
    id: int | None = None
    mode: Literal["brand", "card"] = "brand"
    name: str
    slogan: str
    logo_concept: str
    logo_prompt: str
    color_palette: list[str]
    typography_style: str
    business_card_layout: str
    business_card_copy: BusinessCardCopy
    brand_story: str
    marketing_copy: str
    brand_visual_report: str
    image_url: str | None = None
    created_at: datetime | None = None


class BrandLogoImageIn(BaseModel):
    logo_prompt: Annotated[str, Field(..., min_length=1)]
    record_id: int | None = None
    size: str = "1024*1024"
    n: int = 1


class BrandLogoImageOut(BaseModel):
    image_url: str | None = None
    task_id: str | None = None
    status: str
    message: str = ""
