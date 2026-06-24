from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class BrandVisualRecord(Base):
    __tablename__ = "brand_visual_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    mode: Mapped[str] = mapped_column(String(20), default="brand", index=True)
    name: Mapped[str] = mapped_column(String(100))
    industry: Mapped[str] = mapped_column(String(100), default="")
    style: Mapped[str] = mapped_column(String(200), default="")
    meaning: Mapped[str] = mapped_column(Text, default="")
    slogan: Mapped[str] = mapped_column(String(200), default="")
    logo_prompt: Mapped[str] = mapped_column(Text, default="")
    brand_report: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
