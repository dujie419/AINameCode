"""add open platform

Revision ID: 3f4a2c1d9b80
Revises: 9e11fd12b7aa
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3f4a2c1d9b80"
down_revision: Union[str, Sequence[str], None] = "9e11fd12b7aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "developers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("contact_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_developers")),
        sa.UniqueConstraint("user_id", name=op.f("uq_developers_user_id")),
    )
    op.create_index(op.f("ix_developers_user_id"), "developers", ["user_id"], unique=True)
    op.create_index(op.f("ix_developers_email"), "developers", ["email"], unique=False)

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("developer_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("api_key_prefix", sa.String(length=20), nullable=False),
        sa.Column("api_key_hash", sa.String(length=128), nullable=False),
        sa.Column("secret_key_prefix", sa.String(length=20), nullable=False),
        sa.Column("secret_key_encrypted", sa.Text(), nullable=False),
        sa.Column("secret_key_hash", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("quota", sa.Integer(), nullable=False),
        sa.Column("used_quota", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_keys")),
        sa.UniqueConstraint("api_key_hash", name=op.f("uq_api_keys_api_key_hash")),
        sa.UniqueConstraint("secret_key_hash", name=op.f("uq_api_keys_secret_key_hash")),
    )
    op.create_index(op.f("ix_api_keys_developer_id"), "api_keys", ["developer_id"], unique=False)
    op.create_index(op.f("ix_api_keys_api_key_prefix"), "api_keys", ["api_key_prefix"], unique=False)
    op.create_index(op.f("ix_api_keys_api_key_hash"), "api_keys", ["api_key_hash"], unique=True)

    op.create_table(
        "api_usage_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("developer_id", sa.Integer(), nullable=False),
        sa.Column("api_key_id", sa.Integer(), nullable=False),
        sa.Column("endpoint", sa.String(length=100), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False),
        sa.Column("request_time", sa.DateTime(), nullable=False),
        sa.Column("response_time", sa.Integer(), nullable=False),
        sa.Column("request_ip", sa.String(length=64), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_usage_logs")),
    )
    op.create_index(op.f("ix_api_usage_logs_developer_id"), "api_usage_logs", ["developer_id"], unique=False)
    op.create_index(op.f("ix_api_usage_logs_api_key_id"), "api_usage_logs", ["api_key_id"], unique=False)
    op.create_index(op.f("ix_api_usage_logs_endpoint"), "api_usage_logs", ["endpoint"], unique=False)

    op.create_table(
        "billing_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("developer_id", sa.Integer(), nullable=False),
        sa.Column("api_key_id", sa.Integer(), nullable=False),
        sa.Column("usage_tokens", sa.Integer(), nullable=False),
        sa.Column("cost", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_billing_records")),
    )
    op.create_index(op.f("ix_billing_records_developer_id"), "billing_records", ["developer_id"], unique=False)
    op.create_index(op.f("ix_billing_records_api_key_id"), "billing_records", ["api_key_id"], unique=False)

    plans = op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("quota", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plans")),
        sa.UniqueConstraint("name", name=op.f("uq_plans_name")),
    )
    op.bulk_insert(
        plans,
        [
            {"name": "免费版", "price": 0, "quota": 1000, "description": "1000次/月，适合开发测试"},
            {"name": "专业版", "price": 999, "quota": 100000, "description": "100000次/月，适合中小团队"},
            {"name": "企业版", "price": 0, "quota": 0, "description": "不限量，联系商务定制"},
        ],
    )


def downgrade() -> None:
    op.drop_table("plans")
    op.drop_index(op.f("ix_billing_records_api_key_id"), table_name="billing_records")
    op.drop_index(op.f("ix_billing_records_developer_id"), table_name="billing_records")
    op.drop_table("billing_records")
    op.drop_index(op.f("ix_api_usage_logs_endpoint"), table_name="api_usage_logs")
    op.drop_index(op.f("ix_api_usage_logs_api_key_id"), table_name="api_usage_logs")
    op.drop_index(op.f("ix_api_usage_logs_developer_id"), table_name="api_usage_logs")
    op.drop_table("api_usage_logs")
    op.drop_index(op.f("ix_api_keys_api_key_hash"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_api_key_prefix"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_developer_id"), table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_index(op.f("ix_developers_email"), table_name="developers")
    op.drop_index(op.f("ix_developers_user_id"), table_name="developers")
    op.drop_table("developers")
