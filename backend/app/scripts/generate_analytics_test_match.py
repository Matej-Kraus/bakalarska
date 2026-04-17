from __future__ import annotations

import argparse
import random

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.club import Club
from app.models.match import Match
from app.models.match_event import MatchEvent
from app.models.match_substitution import MatchSubstitution
from app.models.season import Season
from app.util.time import utcnow

from app.scripts.synthetic_match_core import (
    create_substitutions,
    delete_match_data,
    ensure_lineup,
    generate_events,
    get_single_club_and_season,
    plan_substitutions,
)

TEST_MATCH_OPPONENT_DEFAULT = "Analytics Test Match"


def _get_or_create_test_match(
    db: Session,
    club: Club,
    season: Season,
    opponent_name: str,
    replace_existing: bool,
) -> Match:
    existing = (
        db.query(Match)
        .filter(
            Match.club_id == club.id,
            Match.season_id == season.id,
            Match.opponent == opponent_name,
        )
        .order_by(Match.id.asc())
        .first()
    )

    if existing and not replace_existing:
        return existing

    if existing and replace_existing:
        delete_match_data(db, existing.id)
        db.delete(existing)
        db.commit()

    match = Match(
        club_id=club.id,
        season_id=season.id,
        opponent=opponent_name,
        competition="Analytics Test",
        match_date=utcnow(),
        status="finished",
        seconds_before_live=90 * 60,
        live_started_at=None,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a single high-volume synthetic match for analytics testing "
            "(events, substitutions, stats)."
        )
    )
    parser.add_argument(
        "--events",
        type=int,
        default=500,
        help="Approximate number of events to generate (default: 500).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible dataset (default: 42).",
    )
    parser.add_argument(
        "--opponent-name",
        type=str,
        default=TEST_MATCH_OPPONENT_DEFAULT,
        help=f'Opponent name for the test match (default: "{TEST_MATCH_OPPONENT_DEFAULT}").',
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help=(
            "If a test match with the same opponent already exists, delete its data "
            "and regenerate it."
        ),
    )

    args = parser.parse_args()
    rng = random.Random(args.seed)

    db = SessionLocal()
    try:
        club, season = get_single_club_and_season(db)
        match = _get_or_create_test_match(
            db,
            club=club,
            season=season,
            opponent_name=args.opponent_name,
            replace_existing=bool(args.replace_existing),
        )
        lineup_rows = ensure_lineup(db, match, club)

        starter_ids = [lu.player_id for lu in lineup_rows if lu.role == "starter"]
        bench_ids = [lu.player_id for lu in lineup_rows if lu.role == "sub"]

        plans = plan_substitutions(
            starters=starter_ids,
            bench=bench_ids,
            rng=rng,
            min_subs=2,
            max_subs=4,
        )
        create_substitutions(db, match, plans)

        total_events = max(300, args.events)
        generate_events(db, match, lineup_rows, plans, total_events, rng)

        events_count = (
            db.query(MatchEvent).filter(MatchEvent.match_id == match.id).count()
        )
        subs_count = (
            db.query(MatchSubstitution)
            .filter(MatchSubstitution.match_id == match.id)
            .count()
        )

        print("✅ Analytics test match generated")
        print(f"Match ID: {match.id}")
        print(f"Opponent: {match.opponent}")
        print(f"Season ID: {season.id}")
        print(f"Events: {events_count}")
        print(f"Substitutions: {subs_count}")
        print(f"Random seed: {args.seed}")
        print(
            "Tip: open the match in the app (Live/Evaluation/Analytics) and inspect "
            "timelines, team stats and player contributions."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
