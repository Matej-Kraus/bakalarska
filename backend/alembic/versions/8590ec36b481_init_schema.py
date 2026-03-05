"""init_schema

Revision ID: 8590ec36b481
Revises: 
Create Date: 2026-03-02 19:54:56.581946

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8590ec36b481'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "clubs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("name", name="uq_clubs_name"),
    )
    op.create_index("ix_clubs_id", "clubs", ["id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], name="fk_users_club_id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_club_id", "users", ["club_id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "seasons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], name="fk_seasons_club_id"),
        sa.UniqueConstraint("name", name="uq_seasons_name"),
    )
    op.create_index("ix_seasons_id", "seasons", ["id"], unique=False)
    op.create_index("ix_seasons_club_id", "seasons", ["club_id"], unique=False)

    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("jersey_number", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], name="fk_players_club_id"),
    )
    op.create_index("ix_players_id", "players", ["id"], unique=False)
    op.create_index("ix_players_club_id", "players", ["club_id"], unique=False)

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("opponent", sa.String(), nullable=False),
        sa.Column("competition", sa.String(), nullable=True),
        sa.Column("match_date", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="planned"),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], name="fk_matches_club_id"),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"], name="fk_matches_season_id"),
    )
    op.create_index("ix_matches_id", "matches", ["id"], unique=False)
    op.create_index("ix_matches_club_id", "matches", ["club_id"], unique=False)
    op.create_index("ix_matches_season_id", "matches", ["season_id"], unique=False)

    op.create_table(
        "match_lineups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("jersey_number_match", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], name="fk_match_lineups_match_id"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], name="fk_match_lineups_player_id"),
    )
    op.create_index("ix_match_lineups_id", "match_lineups", ["id"], unique=False)
    op.create_index("ix_match_lineups_match_id", "match_lineups", ["match_id"], unique=False)
    op.create_index("ix_match_lineups_player_id", "match_lineups", ["player_id"], unique=False)

    op.create_table(
        "match_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("half", sa.Integer(), nullable=False),
        sa.Column("second_in_match", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], name="fk_match_events_match_id"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], name="fk_match_events_player_id"),
    )
    op.create_index("ix_match_events_id", "match_events", ["id"], unique=False)
    op.create_index("ix_match_events_match_id", "match_events", ["match_id"], unique=False)
    op.create_index("ix_match_events_player_id", "match_events", ["player_id"], unique=False)
    op.create_index("ix_match_events_event_type", "match_events", ["event_type"], unique=False)

    op.create_table(
        "match_player_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("won_balls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lost_balls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fouls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("won_duels", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lost_duels", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shots_on_goal", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shots_off_goal", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("yellow_cards", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("red_cards", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalties", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], name="fk_match_player_stats_match_id"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], name="fk_match_player_stats_player_id"),
        sa.UniqueConstraint(
            "match_id", "player_id", name="uq_match_player_stats_match_player"
        ),
    )
    op.create_index("ix_match_player_stats_id", "match_player_stats", ["id"], unique=False)
    op.create_index(
        "ix_match_player_stats_match_id", "match_player_stats", ["match_id"], unique=False
    )
    op.create_index(
        "ix_match_player_stats_player_id",
        "match_player_stats",
        ["player_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_match_player_stats_player_id", table_name="match_player_stats")
    op.drop_index("ix_match_player_stats_match_id", table_name="match_player_stats")
    op.drop_index("ix_match_player_stats_id", table_name="match_player_stats")
    op.drop_table("match_player_stats")

    op.drop_index("ix_match_events_event_type", table_name="match_events")
    op.drop_index("ix_match_events_player_id", table_name="match_events")
    op.drop_index("ix_match_events_match_id", table_name="match_events")
    op.drop_index("ix_match_events_id", table_name="match_events")
    op.drop_table("match_events")

    op.drop_index("ix_match_lineups_player_id", table_name="match_lineups")
    op.drop_index("ix_match_lineups_match_id", table_name="match_lineups")
    op.drop_index("ix_match_lineups_id", table_name="match_lineups")
    op.drop_table("match_lineups")

    op.drop_index("ix_matches_season_id", table_name="matches")
    op.drop_index("ix_matches_club_id", table_name="matches")
    op.drop_index("ix_matches_id", table_name="matches")
    op.drop_table("matches")

    op.drop_index("ix_players_club_id", table_name="players")
    op.drop_index("ix_players_id", table_name="players")
    op.drop_table("players")

    op.drop_index("ix_seasons_club_id", table_name="seasons")
    op.drop_index("ix_seasons_id", table_name="seasons")
    op.drop_table("seasons")

    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_club_id", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_clubs_id", table_name="clubs")
    op.drop_table("clubs")
