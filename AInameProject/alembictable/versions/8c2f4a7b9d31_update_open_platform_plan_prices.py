"""update open platform plan prices

Revision ID: 8c2f4a7b9d31
Revises: 6a1d8e4f9c20
Create Date: 2026-06-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c2f4a7b9d31"
down_revision: Union[str, Sequence[str], None] = "6a1d8e4f9c20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


plans = sa.table(
    "plans",
    sa.column("name", sa.String),
    sa.column("price", sa.Float),
    sa.column("quota", sa.Integer),
    sa.column("daily_quota", sa.Integer),
    sa.column("qpm_limit", sa.Integer),
    sa.column("token_price", sa.Float),
    sa.column("billing_cycle", sa.String),
    sa.column("status", sa.String),
    sa.column("description", sa.Text),
)


def upgrade() -> None:
    op.execute(
        plans.update()
        .where(plans.c.name == "免费版")
        .values(
            price=0,
            quota=1000,
            daily_quota=100,
            qpm_limit=30,
            token_price=0.0002,
            billing_cycle="month",
            status="active",
            description="1000次/月，适合开发测试",
        )
    )
    op.execute(
        plans.update()
        .where(plans.c.name == "专业版")
        .values(
            price=999,
            quota=100000,
            daily_quota=5000,
            qpm_limit=120,
            token_price=0.0001,
            billing_cycle="month",
            status="active",
            description="100000次/月，适合中小团队",
        )
    )
    op.execute(
        plans.update()
        .where(plans.c.name == "企业版")
        .values(
            price=9999,
            quota=0,
            daily_quota=0,
            qpm_limit=600,
            token_price=0.00008,
            billing_cycle="month",
            status="active",
            description="不限量/月，专属限流策略，适合高频业务接入",
        )
    )


def downgrade() -> None:
    op.execute(
        plans.update()
        .where(plans.c.name == "企业版")
        .values(
            price=0,
            quota=0,
            daily_quota=0,
            qpm_limit=60,
            token_price=0.0001,
            billing_cycle="month",
            status="active",
            description="不限量，联系商务定制",
        )
    )
