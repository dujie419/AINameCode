"""add name records

Revision ID: b8f1d2c3a9e0
Revises: a4f2d8c6e901
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8f1d2c3a9e0"
down_revision: Union[str, Sequence[str], None] = "a4f2d8c6e901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "name_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.String(length=64), nullable=False),
        sa.Column("naming_type", sa.String(length=50), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("keyword", sa.String(length=500), nullable=False),
        sa.Column("surname", sa.String(length=100), nullable=False),
        sa.Column("gender", sa.String(length=30), nullable=False),
        sa.Column("length", sa.String(length=30), nullable=False),
        sa.Column("exclude_words", sa.String(length=500), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("request_json", sa.Text(), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("parent_record_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_name_records")),
    )
    op.create_index(op.f("ix_name_records_user_id"), "name_records", ["user_id"], unique=False)
    op.create_index(op.f("ix_name_records_thread_id"), "name_records", ["thread_id"], unique=False)
    op.create_index(op.f("ix_name_records_naming_type"), "name_records", ["naming_type"], unique=False)
    op.create_index(op.f("ix_name_records_source_type"), "name_records", ["source_type"], unique=False)
    op.create_index(op.f("ix_name_records_status"), "name_records", ["status"], unique=False)
    op.create_index(op.f("ix_name_records_parent_record_id"), "name_records", ["parent_record_id"], unique=False)
    op.create_index(op.f("ix_name_records_created_at"), "name_records", ["created_at"], unique=False)

    op.create_table(
        "name_candidates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("reference", sa.Text(), nullable=False),
        sa.Column("moral", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(length=100), nullable=False),
        sa.Column("domain_status", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_name_candidates")),
    )
    op.create_index(op.f("ix_name_candidates_record_id"), "name_candidates", ["record_id"], unique=False)
    op.create_index(op.f("ix_name_candidates_user_id"), "name_candidates", ["user_id"], unique=False)
    op.create_index(op.f("ix_name_candidates_name"), "name_candidates", ["name"], unique=False)
    op.create_index(op.f("ix_name_candidates_created_at"), "name_candidates", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_name_candidates_created_at"), table_name="name_candidates")
    op.drop_index(op.f("ix_name_candidates_name"), table_name="name_candidates")
    op.drop_index(op.f("ix_name_candidates_user_id"), table_name="name_candidates")
    op.drop_index(op.f("ix_name_candidates_record_id"), table_name="name_candidates")
    op.drop_table("name_candidates")
    op.drop_index(op.f("ix_name_records_created_at"), table_name="name_records")
    op.drop_index(op.f("ix_name_records_parent_record_id"), table_name="name_records")
    op.drop_index(op.f("ix_name_records_status"), table_name="name_records")
    op.drop_index(op.f("ix_name_records_source_type"), table_name="name_records")
    op.drop_index(op.f("ix_name_records_naming_type"), table_name="name_records")
    op.drop_index(op.f("ix_name_records_thread_id"), table_name="name_records")
    op.drop_index(op.f("ix_name_records_user_id"), table_name="name_records")
    op.drop_table("name_records")
