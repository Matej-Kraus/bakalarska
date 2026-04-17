"""add club profile fields

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("clubs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("short_name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("city", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("home_venue", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("founded_year", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("clubs", schema=None) as batch_op:
        batch_op.drop_column("founded_year")
        batch_op.drop_column("home_venue")
        batch_op.drop_column("city")
        batch_op.drop_column("short_name")
