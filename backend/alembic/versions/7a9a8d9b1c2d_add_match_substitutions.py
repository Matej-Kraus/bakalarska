"""add match substitutions

Revision ID: 7a9a8d9b1c2d
Revises: 5c2a4f8b2c3a
Create Date: 2026-03-02 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a9a8d9b1c2d"
down_revision: Union[str, Sequence[str], None] = "5c2a4f8b2c3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "match_substitutions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("player_out_id", sa.Integer(), nullable=False),
        sa.Column("player_in_id", sa.Integer(), nullable=False),
        sa.Column("half", sa.Integer(), nullable=False),
        sa.Column("second_in_match", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.ForeignKeyConstraint(["player_out_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["player_in_id"], ["players.id"]),
    )
    with op.batch_alter_table("match_substitutions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_match_substitutions_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_match_substitutions_match_id"), ["match_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_match_substitutions_player_out_id"), ["player_out_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_match_substitutions_player_in_id"), ["player_in_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("match_substitutions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_match_substitutions_player_in_id"))
        batch_op.drop_index(batch_op.f("ix_match_substitutions_player_out_id"))
        batch_op.drop_index(batch_op.f("ix_match_substitutions_match_id"))
        batch_op.drop_index(batch_op.f("ix_match_substitutions_id"))

    op.drop_table("match_substitutions")

