"""merge usage and community heads

Revision ID: bd4f6a8c2e90
Revises: 1b9d4e7c2a31, ac3e5f7a9b21
Create Date: 2026-06-24 00:00:00.000000
"""

from typing import Sequence, Union


revision: str = "bd4f6a8c2e90"
down_revision: Union[str, Sequence[str], None] = ("1b9d4e7c2a31", "ac3e5f7a9b21")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
