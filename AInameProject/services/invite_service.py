import random
import string
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.growth import (
    DistributionPartner,
    InviteCode,
    InvitationRewardRecord,
    PartnerAttribution,
    ReferralRelation,
    UserQuotaGrant,
)
from models.user import User


INVITE_REWARD_AMOUNT = 3
INVITE_REWARD_USAGE_TYPE = "name_generate"


def normalize_invite_code(code: str | None) -> str:
    return (code or "").strip().upper()


def random_invite_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def normalize_partner_code(code: str | None) -> str:
    return (code or "").strip().upper()


def partner_qr_payload(partner_code: str) -> str:
    return f"/pages/register/register?partner_code={partner_code}"


async def random_partner_code(session: AsyncSession, length: int = 10) -> str:
    for _ in range(10):
        code = f"P{random_invite_code(length - 1)}"
        duplicate = await session.scalar(select(DistributionPartner).where(DistributionPartner.partner_code == code))
        if not duplicate:
            return code
    raise RuntimeError("Unable to generate unique partner code")


async def get_or_create_invite_code(user_id: int, session: AsyncSession) -> InviteCode:
    exists = await session.scalar(select(InviteCode).where(InviteCode.user_id == int(user_id)))
    if exists:
        return exists

    for _ in range(10):
        code = random_invite_code()
        duplicate = await session.scalar(select(InviteCode).where(InviteCode.code == code))
        if not duplicate:
            invite_code = InviteCode(user_id=int(user_id), code=code, status="active")
            session.add(invite_code)
            await session.flush()
            return invite_code
    raise RuntimeError("Unable to generate unique invite code")


async def bind_inviter_and_grant_reward(
        invitee: User,
        invite_code: str | None,
        session: AsyncSession,
        source: str = "register",
) -> ReferralRelation | None:
    code = normalize_invite_code(invite_code)
    if not code:
        return None

    inviter_code = await session.scalar(
        select(InviteCode).where(InviteCode.code == code, InviteCode.status == "active")
    )
    if not inviter_code:
        return None
    if int(inviter_code.user_id) == int(invitee.id):
        return None

    exists = await session.scalar(
        select(ReferralRelation).where(ReferralRelation.invitee_user_id == int(invitee.id))
    )
    if exists:
        return exists

    relation = ReferralRelation(
        inviter_user_id=int(inviter_code.user_id),
        invitee_user_id=int(invitee.id),
        invite_code=code,
        source=source,
        reward_status="pending",
    )
    session.add(relation)
    await session.flush()

    reward = InvitationRewardRecord(
        relation_id=relation.id,
        inviter_user_id=relation.inviter_user_id,
        invitee_user_id=relation.invitee_user_id,
        reward_target_user_id=relation.inviter_user_id,
        reward_type=f"{INVITE_REWARD_USAGE_TYPE}_quota",
        amount=INVITE_REWARD_AMOUNT,
        status="granted",
        reason="invite registration reward",
    )
    session.add(reward)
    await session.flush()

    session.add(UserQuotaGrant(
        user_id=relation.inviter_user_id,
        usage_type=INVITE_REWARD_USAGE_TYPE,
        grant_type="invite_reward",
        total_amount=INVITE_REWARD_AMOUNT,
        used_amount=0,
        status="active",
        source_id=reward.id,
        reason=f"Invite reward for user {relation.invitee_user_id}",
    ))
    relation.reward_status = "granted"
    relation.rewarded_at = datetime.now()
    return relation


async def bind_partner_attribution(
        user: User,
        partner_code: str | None,
        session: AsyncSession,
        source: str = "register",
) -> PartnerAttribution | None:
    code = normalize_partner_code(partner_code)
    if not code:
        return None

    partner = await session.scalar(
        select(DistributionPartner).where(
            DistributionPartner.partner_code == code,
            DistributionPartner.status == "approved",
        )
    )
    if not partner:
        return None
    if int(partner.user_id) == int(user.id):
        return None

    exists = await session.scalar(select(PartnerAttribution).where(PartnerAttribution.user_id == int(user.id)))
    if exists:
        return exists

    attribution = PartnerAttribution(
        partner_id=partner.id,
        partner_user_id=partner.user_id,
        user_id=int(user.id),
        partner_code=code,
        source=source,
        first_event="register",
    )
    session.add(attribution)
    await session.flush()
    return attribution
