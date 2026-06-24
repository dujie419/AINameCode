from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Expert(Base):
    __tablename__ = "experts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(100))
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    tags: Mapped[str] = mapped_column(String(500), default="")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("99.00"))
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    rating: Mapped[float] = mapped_column(Float, default=5.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ExpertOrder(Base):
    __tablename__ = "expert_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    expert_id: Mapped[int] = mapped_column(Integer, index=True)
    name_record_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    fee_rule_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    fee_rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.2000"))
    platform_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    expert_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    report_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    report_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_suggestions: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    settlement_due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ExpertReview(Base):
    __tablename__ = "expert_reviews"
    __table_args__ = (UniqueConstraint("expert_order_id", "user_id", name="uq_expert_reviews_order_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expert_id: Mapped[int] = mapped_column(Integer, index=True)
    expert_order_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    rating: Mapped[int] = mapped_column(Integer, default=5)
    content: Mapped[str] = mapped_column(Text, default="")
    reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="visible", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AfterSaleRequest(Base):
    __tablename__ = "after_sale_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    expert_id: Mapped[int] = mapped_column(Integer, index=True)
    expert_order_id: Mapped[int] = mapped_column(Integer, index=True)
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    request_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    request_type: Mapped[str] = mapped_column(String(30), index=True)
    reason: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    naming_type: Mapped[str] = mapped_column(String(50), default="企业名", index=True)
    name_record_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CommunityCandidate(Base):
    __tablename__ = "community_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, index=True)
    name_candidate_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    reference: Mapped[str] = mapped_column(Text, default="")
    moral: Mapped[str] = mapped_column(Text, default="")
    domain: Mapped[str] = mapped_column(String(100), default="")
    vote_count: Mapped[int] = mapped_column(Integer, default=0)


class CommunityVote(Base):
    __tablename__ = "community_votes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_community_votes_post_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, index=True)
    candidate_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
