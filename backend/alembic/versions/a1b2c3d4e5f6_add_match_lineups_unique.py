"""add match_lineups unique (match_id, player_id)

Revision ID: a1b2c3d4e5f6
Revises: 7a9a8d9b1c2d
Create Date: 2026-03-03

"""
from typing import Sequence, Union

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7a9a8d9b1c2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("match_lineups", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_match_lineups_match_player",
            ["match_id", "player_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("match_lineups", schema=None) as batch_op:
        batch_op.drop_constraint("uq_match_lineups_match_player", type_="unique")
