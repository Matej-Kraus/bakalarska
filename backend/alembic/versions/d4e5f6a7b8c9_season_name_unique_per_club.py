"""season name unique per club

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-13
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("seasons", schema=None) as batch_op:
        batch_op.drop_constraint("uq_seasons_name", type_="unique")
        batch_op.create_unique_constraint("uq_seasons_club_name", ["club_id", "name"])


def downgrade() -> None:
    with op.batch_alter_table("seasons", schema=None) as batch_op:
        batch_op.drop_constraint("uq_seasons_club_name", type_="unique")
        batch_op.create_unique_constraint("uq_seasons_name", ["name"])
