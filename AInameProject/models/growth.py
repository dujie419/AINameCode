from datetime import datetime

from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class InviteCode(Base):
    __tablename__ = "invite_codes"
    __table_args__ = (UniqueConstraint("user_id", name="uq_invite_codes_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ReferralRelation(Base):
    __tablename__ = "referral_relations"
    __table_args__ = (
        UniqueConstraint("invitee_user_id", name="uq_referral_relations_invitee_user_id"),
        UniqueConstraint("inviter_user_id", "invitee_user_id", name="uq_referral_relations_inviter_invitee"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inviter_user_id: Mapped[int] = mapped_column(Integer, index=True)
    invitee_user_id: Mapped[int] = mapped_column(Integer, index=True)
    invite_code: Mapped[str] = mapped_column(String(32), index=True)
    source: Mapped[str] = mapped_column(String(50), default="invite_link", index=True)
    reward_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    rewarded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class InvitationRewardRecord(Base):
    __tablename__ = "invitation_reward_records"
    __table_args__ = (
        UniqueConstraint("relation_id", "reward_target_user_id", "reward_type", name="uq_invitation_rewards_relation_target_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    relation_id: Mapped[int] = mapped_column(Integer, index=True)
    inviter_user_id: Mapped[int] = mapped_column(Integer, index=True)
    invitee_user_id: Mapped[int] = mapped_column(Integer, index=True)
    reward_target_user_id: Mapped[int] = mapped_column(Integer, index=True)
    reward_type: Mapped[str] = mapped_column(String(50), default="name_generate_quota", index=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="granted", index=True)
    reason: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class UserQuotaGrant(Base):
    __tablename__ = "user_quota_grants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    usage_type: Mapped[str] = mapped_column(String(50), index=True)
    grant_type: Mapped[str] = mapped_column(String(50), index=True)
    total_amount: Mapped[int] = mapped_column(Integer)
    used_amount: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    reason: Mapped[str] = mapped_column(String(255), default="")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class DistributionPartner(Base):
    __tablename__ = "distribution_partners"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_distribution_partners_user_id"),
        UniqueConstraint("partner_code", name="uq_distribution_partners_partner_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    partner_type: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(100))
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    partner_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    qr_payload: Mapped[str] = mapped_column(String(500), default="")
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.1000"))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class PartnerAttribution(Base):
    __tablename__ = "partner_attributions"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_partner_attributions_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    partner_id: Mapped[int] = mapped_column(Integer, index=True)
    partner_user_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    partner_code: Mapped[str] = mapped_column(String(32), index=True)
    source: Mapped[str] = mapped_column(String(50), default="partner_qr", index=True)
    first_event: Mapped[str] = mapped_column(String(50), default="register", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)


class PartnerCommissionRecord(Base):
    __tablename__ = "partner_commission_records"
    __table_args__ = (
        UniqueConstraint("business_type", "business_id", name="uq_partner_commissions_business"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    partner_id: Mapped[int] = mapped_column(Integer, index=True)
    partner_user_id: Mapped[int] = mapped_column(Integer, index=True)
    buyer_user_id: Mapped[int] = mapped_column(Integer, index=True)
    attribution_id: Mapped[int] = mapped_column(Integer, index=True)
    business_type: Mapped[str] = mapped_column(String(50), index=True)
    business_id: Mapped[int] = mapped_column(Integer, index=True)
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    payment_order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(30), default="settle_pending", index=True)
    settlement_due_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reverse_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)


class PartnerWithdrawal(Base):
    __tablename__ = "partner_withdrawals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    partner_id: Mapped[int] = mapped_column(Integer, index=True)
    partner_user_id: Mapped[int] = mapped_column(Integer, index=True)
    withdrawal_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    account_name: Mapped[str] = mapped_column(String(100))
    account_no: Mapped[str] = mapped_column(String(100))
    bank_name: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_trade_no: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
