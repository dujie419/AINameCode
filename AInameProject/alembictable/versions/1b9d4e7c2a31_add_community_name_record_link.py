"""add community name record link

Revision ID: 1b9d4e7c2a31
Revises: f6b2d9a1c8e4
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError


revision: str = "1b9d4e7c2a31"
down_revision: Union[str, Sequence[str], None] = "f6b2d9a1c8e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in [column["name"] for column in inspector.get_columns(table_name)]


def has_index(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in [index["name"] for index in inspector.get_indexes(table_name)]


def add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not has_column(table_name, column.name):
        try:
            op.add_column(table_name, column)
        except OperationalError as error:
            if getattr(error.orig, "args", [None])[0] != 1060:
                raise


def create_index_if_missing(table_name: str, index_name: str, columns: list[str]) -> None:
    if not has_index(table_name, index_name):
        try:
            op.create_index(index_name, table_name, columns, unique=False)
        except OperationalError as error:
            if getattr(error.orig, "args", [None])[0] != 1061:
                raise


def drop_column_if_exists(table_name: str, column_name: str) -> None:
    if has_column(table_name, column_name):
        try:
            op.drop_column(table_name, column_name)
        except OperationalError as error:
            if getattr(error.orig, "args", [None])[0] != 1091:
                raise


def drop_index_if_exists(table_name: str, index_name: str) -> None:
    if has_index(table_name, index_name):
        try:
            op.drop_index(index_name, table_name=table_name)
        except OperationalError as error:
            if getattr(error.orig, "args", [None])[0] != 1091:
                raise


def upgrade() -> None:
    add_column_if_missing("community_posts", sa.Column("naming_type", sa.String(length=50), nullable=False, server_default="企业名"))
    add_column_if_missing("community_posts", sa.Column("name_record_id", sa.Integer(), nullable=True))
    create_index_if_missing("community_posts", "ix_community_posts_naming_type", ["naming_type"])
    create_index_if_missing("community_posts", "ix_community_posts_name_record_id", ["name_record_id"])

    add_column_if_missing("community_candidates", sa.Column("name_candidate_id", sa.Integer(), nullable=True))
    add_column_if_missing("community_candidates", sa.Column("reference", sa.Text(), nullable=True))
    add_column_if_missing("community_candidates", sa.Column("moral", sa.Text(), nullable=True))
    add_column_if_missing("community_candidates", sa.Column("domain", sa.String(length=100), nullable=False, server_default=""))
    create_index_if_missing("community_candidates", "ix_community_candidates_name_candidate_id", ["name_candidate_id"])


def downgrade() -> None:
    drop_index_if_exists("community_candidates", "ix_community_candidates_name_candidate_id")
    drop_column_if_exists("community_candidates", "domain")
    drop_column_if_exists("community_candidates", "moral")
    drop_column_if_exists("community_candidates", "reference")
    drop_column_if_exists("community_candidates", "name_candidate_id")

    drop_index_if_exists("community_posts", "ix_community_posts_name_record_id")
    drop_index_if_exists("community_posts", "ix_community_posts_naming_type")
    drop_column_if_exists("community_posts", "name_record_id")
    drop_column_if_exists("community_posts", "naming_type")
