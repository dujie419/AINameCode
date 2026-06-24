from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class NameRecord(Base):
    __tablename__ = "name_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    thread_id: Mapped[str] = mapped_column(String(64), index=True)
    naming_type: Mapped[str] = mapped_column(String(50), index=True)
    source_type: Mapped[str] = mapped_column(String(30), default="generate", index=True)
    keyword: Mapped[str] = mapped_column(String(500), default="")
    surname: Mapped[str] = mapped_column(String(100), default="")
    gender: Mapped[str] = mapped_column(String(30), default="")
    length: Mapped[str] = mapped_column(String(30), default="")
    exclude_words: Mapped[str] = mapped_column(String(500), default="")
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(20), default="success", index=True)
    parent_record_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)


class NameCandidate(Base):
    __tablename__ = "name_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    reference: Mapped[str] = mapped_column(Text, default="")
    moral: Mapped[str] = mapped_column(Text, default="")
    domain: Mapped[str] = mapped_column(String(100), default="")
    domain_status: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
