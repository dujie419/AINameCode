"""add distribution partners

Revision ID: 0f3e9d2c7b11
Revises: g4c8e2a1b5d0
Create Date: 2026-06-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0f3e9d2c7b11"
down_revision: Union[str, Sequence[str], None] = "g4c8e2a1b5d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "distribution_partners",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("partner_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("contact_phone", sa.String(length=30), nullable=True),
        sa.Column("company_name", sa.String(length=200), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("partner_code", sa.String(length=32), nullable=False),
        sa.Column("qr_payload", sa.String(length=500), nullable=False),
        sa.Column("commission_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_distribution_partners")),
        sa.UniqueConstraint("user_id", name="uq_distribution_partners_user_id"),
        sa.UniqueConstraint("partner_code", name="uq_distribution_partners_partner_code"),
    )
    op.create_index(op.f("ix_distribution_partners_user_id"), "distribution_partners", ["user_id"], unique=False)
    op.create_index(op.f("ix_distribution_partners_partner_type"), "distribution_partners", ["partner_type"], unique=False)
    op.create_index(op.f("ix_distribution_partners_partner_code"), "distribution_partners", ["partner_code"], unique=True)
    op.create_index(op.f("ix_distribution_partners_status"), "distribution_partners", ["status"], unique=False)

    op.create_table(
        "partner_attributions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("partner_user_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("partner_code", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("first_event", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_partner_attributions")),
        sa.UniqueConstraint("user_id", name="uq_partner_attributions_user_id"),
    )
    op.create_index(op.f("ix_partner_attributions_partner_id"), "partner_attributions", ["partner_id"], unique=False)
    op.create_index(op.f("ix_partner_attributions_partner_user_id"), "partner_attributions", ["partner_user_id"], unique=False)
    op.create_index(op.f("ix_partner_attributions_user_id"), "partner_attributions", ["user_id"], unique=False)
    op.create_index(op.f("ix_partner_attributions_partner_code"), "partner_attributions", ["partner_code"], unique=False)
    op.create_index(op.f("ix_partner_attributions_source"), "partner_attributions", ["source"], unique=False)
    op.create_index(op.f("ix_partner_attributions_first_event"), "partner_attributions", ["first_event"], unique=False)
    op.create_index(op.f("ix_partner_attributions_created_at"), "partner_attributions", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_partner_attributions_created_at"), table_name="partner_attributions")
    op.drop_index(op.f("ix_partner_attributions_first_event"), table_name="partner_attributions")
    op.drop_index(op.f("ix_partner_attributions_source"), table_name="partner_attributions")
    op.drop_index(op.f("ix_partner_attributions_partner_code"), table_name="partner_attributions")
    op.drop_index(op.f("ix_partner_attributions_user_id"), table_name="partner_attributions")
    op.drop_index(op.f("ix_partner_attributions_partner_user_id"), table_name="partner_attributions")
    op.drop_index(op.f("ix_partner_attributions_partner_id"), table_name="partner_attributions")
    op.drop_table("partner_attributions")

    op.drop_index(op.f("ix_distribution_partners_status"), table_name="distribution_partners")
    op.drop_index(op.f("ix_distribution_partners_partner_code"), table_name="distribution_partners")
    op.drop_index(op.f("ix_distribution_partners_partner_type"), table_name="distribution_partners")
    op.drop_index(op.f("ix_distribution_partners_user_id"), table_name="distribution_partners")
    op.drop_table("distribution_partners")
