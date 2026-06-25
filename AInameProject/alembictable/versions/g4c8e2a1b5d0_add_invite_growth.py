"""add invite growth

Revision ID: g4c8e2a1b5d0
Revises: f6b2d9a1c8e4, cf7a1b3d5e92
Create Date: 2026-06-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g4c8e2a1b5d0"
down_revision: Union[str, Sequence[str], None] = ("f6b2d9a1c8e4", "cf7a1b3d5e92")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invite_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invite_codes")),
        sa.UniqueConstraint("user_id", name="uq_invite_codes_user_id"),
    )
    op.create_index(op.f("ix_invite_codes_user_id"), "invite_codes", ["user_id"], unique=False)
    op.create_index(op.f("ix_invite_codes_code"), "invite_codes", ["code"], unique=True)
    op.create_index(op.f("ix_invite_codes_status"), "invite_codes", ["status"], unique=False)

    op.create_table(
        "referral_relations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("inviter_user_id", sa.Integer(), nullable=False),
        sa.Column("invitee_user_id", sa.Integer(), nullable=False),
        sa.Column("invite_code", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("reward_status", sa.String(length=20), nullable=False),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.Column("rewarded_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_referral_relations")),
        sa.UniqueConstraint("invitee_user_id", name="uq_referral_relations_invitee_user_id"),
        sa.UniqueConstraint("inviter_user_id", "invitee_user_id", name="uq_referral_relations_inviter_invitee"),
    )
    op.create_index(op.f("ix_referral_relations_inviter_user_id"), "referral_relations", ["inviter_user_id"], unique=False)
    op.create_index(op.f("ix_referral_relations_invitee_user_id"), "referral_relations", ["invitee_user_id"], unique=False)
    op.create_index(op.f("ix_referral_relations_invite_code"), "referral_relations", ["invite_code"], unique=False)
    op.create_index(op.f("ix_referral_relations_source"), "referral_relations", ["source"], unique=False)
    op.create_index(op.f("ix_referral_relations_reward_status"), "referral_relations", ["reward_status"], unique=False)
    op.create_index(op.f("ix_referral_relations_registered_at"), "referral_relations", ["registered_at"], unique=False)

    op.create_table(
        "invitation_reward_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("relation_id", sa.Integer(), nullable=False),
        sa.Column("inviter_user_id", sa.Integer(), nullable=False),
        sa.Column("invitee_user_id", sa.Integer(), nullable=False),
        sa.Column("reward_target_user_id", sa.Integer(), nullable=False),
        sa.Column("reward_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invitation_reward_records")),
        sa.UniqueConstraint("relation_id", "reward_target_user_id", "reward_type", name="uq_invitation_rewards_relation_target_type"),
    )
    op.create_index(op.f("ix_invitation_reward_records_relation_id"), "invitation_reward_records", ["relation_id"], unique=False)
    op.create_index(op.f("ix_invitation_reward_records_inviter_user_id"), "invitation_reward_records", ["inviter_user_id"], unique=False)
    op.create_index(op.f("ix_invitation_reward_records_invitee_user_id"), "invitation_reward_records", ["invitee_user_id"], unique=False)
    op.create_index(op.f("ix_invitation_reward_records_reward_target_user_id"), "invitation_reward_records", ["reward_target_user_id"], unique=False)
    op.create_index(op.f("ix_invitation_reward_records_reward_type"), "invitation_reward_records", ["reward_type"], unique=False)
    op.create_index(op.f("ix_invitation_reward_records_status"), "invitation_reward_records", ["status"], unique=False)

    op.create_table(
        "user_quota_grants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("usage_type", sa.String(length=50), nullable=False),
        sa.Column("grant_type", sa.String(length=50), nullable=False),
        sa.Column("total_amount", sa.Integer(), nullable=False),
        sa.Column("used_amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_quota_grants")),
    )
    op.create_index(op.f("ix_user_quota_grants_user_id"), "user_quota_grants", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_quota_grants_usage_type"), "user_quota_grants", ["usage_type"], unique=False)
    op.create_index(op.f("ix_user_quota_grants_grant_type"), "user_quota_grants", ["grant_type"], unique=False)
    op.create_index(op.f("ix_user_quota_grants_status"), "user_quota_grants", ["status"], unique=False)
    op.create_index(op.f("ix_user_quota_grants_source_id"), "user_quota_grants", ["source_id"], unique=False)
    op.create_index(op.f("ix_user_quota_grants_expires_at"), "user_quota_grants", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_quota_grants_expires_at"), table_name="user_quota_grants")
    op.drop_index(op.f("ix_user_quota_grants_source_id"), table_name="user_quota_grants")
    op.drop_index(op.f("ix_user_quota_grants_status"), table_name="user_quota_grants")
    op.drop_index(op.f("ix_user_quota_grants_grant_type"), table_name="user_quota_grants")
    op.drop_index(op.f("ix_user_quota_grants_usage_type"), table_name="user_quota_grants")
    op.drop_index(op.f("ix_user_quota_grants_user_id"), table_name="user_quota_grants")
    op.drop_table("user_quota_grants")
    op.drop_index(op.f("ix_invitation_reward_records_status"), table_name="invitation_reward_records")
    op.drop_index(op.f("ix_invitation_reward_records_reward_type"), table_name="invitation_reward_records")
    op.drop_index(op.f("ix_invitation_reward_records_reward_target_user_id"), table_name="invitation_reward_records")
    op.drop_index(op.f("ix_invitation_reward_records_invitee_user_id"), table_name="invitation_reward_records")
    op.drop_index(op.f("ix_invitation_reward_records_inviter_user_id"), table_name="invitation_reward_records")
    op.drop_index(op.f("ix_invitation_reward_records_relation_id"), table_name="invitation_reward_records")
    op.drop_table("invitation_reward_records")
    op.drop_index(op.f("ix_referral_relations_registered_at"), table_name="referral_relations")
    op.drop_index(op.f("ix_referral_relations_reward_status"), table_name="referral_relations")
    op.drop_index(op.f("ix_referral_relations_source"), table_name="referral_relations")
    op.drop_index(op.f("ix_referral_relations_invite_code"), table_name="referral_relations")
    op.drop_index(op.f("ix_referral_relations_invitee_user_id"), table_name="referral_relations")
    op.drop_index(op.f("ix_referral_relations_inviter_user_id"), table_name="referral_relations")
    op.drop_table("referral_relations")
    op.drop_index(op.f("ix_invite_codes_status"), table_name="invite_codes")
    op.drop_index(op.f("ix_invite_codes_code"), table_name="invite_codes")
    op.drop_index(op.f("ix_invite_codes_user_id"), table_name="invite_codes")
    op.drop_table("invite_codes")
