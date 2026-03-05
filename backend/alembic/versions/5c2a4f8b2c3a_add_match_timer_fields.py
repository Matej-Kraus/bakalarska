"""add match timer fields

Revision ID: 5c2a4f8b2c3a
Revises: 9f71c8c64a15
Create Date: 2026-03-02 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5c2a4f8b2c3a"
down_revision: Union[str, Sequence[str], None] = "9f71c8c64a15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("matches", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("seconds_before_live", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(sa.Column("live_started_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("matches", schema=None) as batch_op:
        batch_op.drop_column("live_started_at")
        batch_op.drop_column("seconds_before_live")

