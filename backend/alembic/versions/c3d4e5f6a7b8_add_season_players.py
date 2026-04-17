"""add season_players

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-08 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "season_players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("season_id", "player_id", name="uq_season_players_season_player"),
    )
    op.create_index(op.f("ix_season_players_id"), "season_players", ["id"], unique=False)
    op.create_index(op.f("ix_season_players_season_id"), "season_players", ["season_id"], unique=False)
    op.create_index(op.f("ix_season_players_player_id"), "season_players", ["player_id"], unique=False)

    # Backfill: keep current behavior by assigning all existing club players
    # to all existing seasons of the same club.
    op.execute(
        """
        INSERT INTO season_players (season_id, player_id)
        SELECT s.id, p.id
        FROM seasons s
        JOIN players p ON p.club_id = s.club_id
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_season_players_player_id"), table_name="season_players")
    op.drop_index(op.f("ix_season_players_season_id"), table_name="season_players")
    op.drop_index(op.f("ix_season_players_id"), table_name="season_players")
    op.drop_table("season_players")

