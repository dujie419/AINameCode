"""add open platform billing and limits

Revision ID: e1f6a9b2c4d7
Revises: d4a7c8f2e6b3
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1f6a9b2c4d7"
down_revision: Union[str, Sequence[str], None] = "d4a7c8f2e6b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("developers", sa.Column("plan_id", sa.Integer(), nullable=True))
    op.add_column("developers", sa.Column("subscription_status", sa.String(length=20), nullable=False, server_default="inactive"))
    op.add_column("developers", sa.Column("subscription_expires_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_developers_plan_id"), "developers", ["plan_id"], unique=False)
    op.create_index(op.f("ix_developers_subscription_status"), "developers", ["subscription_status"], unique=False)

    op.add_column("plans", sa.Column("daily_quota", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("plans", sa.Column("qpm_limit", sa.Integer(), nullable=False, server_default="60"))
    op.add_column("plans", sa.Column("token_price", sa.Float(), nullable=False, server_default="0.0001"))
    op.add_column("plans", sa.Column("billing_cycle", sa.String(length=20), nullable=False, server_default="month"))
    op.add_column("plans", sa.Column("status", sa.String(length=20), nullable=False, server_default="active"))
    op.create_index(op.f("ix_plans_status"), "plans", ["status"], unique=False)

    op.create_table(
        "developer_subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("developer_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_developer_subscriptions")),
    )
    op.create_index(op.f("ix_developer_subscriptions_developer_id"), "developer_subscriptions", ["developer_id"], unique=False)
    op.create_index(op.f("ix_developer_subscriptions_plan_id"), "developer_subscriptions", ["plan_id"], unique=False)
    op.create_index(op.f("ix_developer_subscriptions_status"), "developer_subscriptions", ["status"], unique=False)
    op.create_index(op.f("ix_developer_subscriptions_expires_at"), "developer_subscriptions", ["expires_at"], unique=False)

    op.create_table(
        "api_rate_limit_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("developer_id", sa.Integer(), nullable=True),
        sa.Column("api_key_id", sa.Integer(), nullable=True),
        sa.Column("endpoint", sa.String(length=100), nullable=False),
        sa.Column("qpm_limit", sa.Integer(), nullable=False),
        sa.Column("daily_quota", sa.Integer(), nullable=False),
        sa.Column("monthly_quota", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_rate_limit_rules")),
    )
    op.create_index(op.f("ix_api_rate_limit_rules_developer_id"), "api_rate_limit_rules", ["developer_id"], unique=False)
    op.create_index(op.f("ix_api_rate_limit_rules_api_key_id"), "api_rate_limit_rules", ["api_key_id"], unique=False)
    op.create_index(op.f("ix_api_rate_limit_rules_endpoint"), "api_rate_limit_rules", ["endpoint"], unique=False)
    op.create_index(op.f("ix_api_rate_limit_rules_status"), "api_rate_limit_rules", ["status"], unique=False)

    op.create_table(
        "api_billing_summaries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("developer_id", sa.Integer(), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("total_calls", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("total_cost", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_billing_summaries")),
    )
    op.create_index(op.f("ix_api_billing_summaries_developer_id"), "api_billing_summaries", ["developer_id"], unique=False)
    op.create_index(op.f("ix_api_billing_summaries_period"), "api_billing_summaries", ["period"], unique=False)
    op.create_index(op.f("ix_api_billing_summaries_status"), "api_billing_summaries", ["status"], unique=False)

    op.create_table(
        "api_reconciliation_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("developer_id", sa.Integer(), nullable=True),
        sa.Column("usage_log_count", sa.Integer(), nullable=False),
        sa.Column("billing_record_count", sa.Integer(), nullable=False),
        sa.Column("usage_tokens", sa.Integer(), nullable=False),
        sa.Column("billed_tokens", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_reconciliation_records")),
    )
    op.create_index(op.f("ix_api_reconciliation_records_period"), "api_reconciliation_records", ["period"], unique=False)
    op.create_index(op.f("ix_api_reconciliation_records_developer_id"), "api_reconciliation_records", ["developer_id"], unique=False)
    op.create_index(op.f("ix_api_reconciliation_records_status"), "api_reconciliation_records", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_api_reconciliation_records_status"), table_name="api_reconciliation_records")
    op.drop_index(op.f("ix_api_reconciliation_records_developer_id"), table_name="api_reconciliation_records")
    op.drop_index(op.f("ix_api_reconciliation_records_period"), table_name="api_reconciliation_records")
    op.drop_table("api_reconciliation_records")
    op.drop_index(op.f("ix_api_billing_summaries_status"), table_name="api_billing_summaries")
    op.drop_index(op.f("ix_api_billing_summaries_period"), table_name="api_billing_summaries")
    op.drop_index(op.f("ix_api_billing_summaries_developer_id"), table_name="api_billing_summaries")
    op.drop_table("api_billing_summaries")
    op.drop_index(op.f("ix_api_rate_limit_rules_status"), table_name="api_rate_limit_rules")
    op.drop_index(op.f("ix_api_rate_limit_rules_endpoint"), table_name="api_rate_limit_rules")
    op.drop_index(op.f("ix_api_rate_limit_rules_api_key_id"), table_name="api_rate_limit_rules")
    op.drop_index(op.f("ix_api_rate_limit_rules_developer_id"), table_name="api_rate_limit_rules")
    op.drop_table("api_rate_limit_rules")
    op.drop_index(op.f("ix_developer_subscriptions_expires_at"), table_name="developer_subscriptions")
    op.drop_index(op.f("ix_developer_subscriptions_status"), table_name="developer_subscriptions")
    op.drop_index(op.f("ix_developer_subscriptions_plan_id"), table_name="developer_subscriptions")
    op.drop_index(op.f("ix_developer_subscriptions_developer_id"), table_name="developer_subscriptions")
    op.drop_table("developer_subscriptions")
    op.drop_index(op.f("ix_plans_status"), table_name="plans")
    op.drop_column("plans", "status")
    op.drop_column("plans", "billing_cycle")
    op.drop_column("plans", "token_price")
    op.drop_column("plans", "qpm_limit")
    op.drop_column("plans", "daily_quota")
    op.drop_index(op.f("ix_developers_subscription_status"), table_name="developers")
    op.drop_index(op.f("ix_developers_plan_id"), table_name="developers")
    op.drop_column("developers", "subscription_expires_at")
    op.drop_column("developers", "subscription_status")
    op.drop_column("developers", "plan_id")
