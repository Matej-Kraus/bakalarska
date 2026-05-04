from __future__ import annotations

import argparse
import random
from datetime import timedelta

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.match import Match
from app.models.season import Season
from app.models.user import User
from app.scripts.sim_match_core_v2 import (
    build_player_position_map,
    create_substitutions,
    delete_match_data,
    ensure_lineup,
    generate_events,
    plan_substitutions,
    sample_match_profile,
)
from app.util.time import utcnow


def _get_coach_club_and_season(db: Session) -> tuple[int, Season]:
    coach = db.query(User).filter(User.email == "coach@demo.local").first()
    if coach:
        season = (
            db.query(Season)
            .filter(Season.club_id == coach.club_id)
            .order_by(Season.id.asc())
            .first()
        )
        if season:
            return coach.club_id, season

    season = db.query(Season).order_by(Season.id.asc()).first()
    if not season:
        raise RuntimeError("No season found. Run seed first.")
    return season.club_id, season


def _resolve_season_for_club(db: Session, club_id: int, season_id: int | None) -> Season:
    if season_id is not None:
        season = (
            db.query(Season)
            .filter(Season.id == season_id, Season.club_id == club_id)
            .first()
        )
        if not season:
            raise RuntimeError(
                f"Season id={season_id} was not found for club_id={club_id}."
            )
        return season

    season = (
        db.query(Season)
        .filter(Season.club_id == club_id)
        .order_by(Season.id.asc())
        .first()
    )
    if not season:
        raise RuntimeError(f"No season found for club_id={club_id}.")
    return season


def _delete_all_matches_for_club_season(db: Session, club_id: int, season_id: int) -> int:
    rows = (
        db.query(Match)
        .filter(Match.club_id == club_id, Match.season_id == season_id)
        .order_by(Match.id.asc())
        .all()
    )
    for m in rows:
        delete_match_data(db, m.id)
        db.delete(m)
    db.commit()
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate full 90-minute synthetic season matches for demo and analytics."
    )
    parser.add_argument("--matches", type=int, default=15, help="Number of matches to generate.")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed for reproducibility.")
    parser.add_argument(
        "--season-id",
        type=int,
        default=None,
        help="Target season id. If omitted, first season for selected club is used.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Delete existing matches in selected club+season before generation.",
    )
    parser.add_argument(
        "--min-events",
        type=int,
        default=520,
        help="Minimum events per match (realistic full-match dataset).",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=820,
        help="Maximum events per match (realistic full-match dataset).",
    )
    args = parser.parse_args()

    if args.matches <= 0:
        raise ValueError("--matches must be > 0")
    if args.min_events <= 0 or args.max_events < args.min_events:
        raise ValueError("Invalid event bounds")

    rng = random.Random(args.seed)
    opponents = [
        "Sparta",
        "Slavia",
        "Plzen",
        "Liberec",
        "Olomouc",
        "Bohemians",
        "Jablonec",
        "Boleslav",
        "Brno",
        "Pardubice",
        "Teplice",
        "Hradec",
        "Karvina",
        "Zlin",
        "Opava",
        "Dukla",
        "Banik",
        "Sigma",
        "Viktoria",
        "Slovan",
    ]
    competitions = ["Liga", "Pohar", "Pratelsky zapas"]

    db = SessionLocal()
    try:
        club_id, _fallback_season = _get_coach_club_and_season(db)
        season = _resolve_season_for_club(db, club_id, args.season_id)
        deleted = 0
        if args.replace_existing:
            deleted = _delete_all_matches_for_club_season(db, club_id, season.id)

        start_date = utcnow() - timedelta(days=args.matches * 7)
        created_ids: list[int] = []

        for i in range(args.matches):
            m = Match(
                club_id=club_id,
                season_id=season.id,
                opponent=opponents[i % len(opponents)],
                competition=rng.choice(competitions),
                match_date=start_date + timedelta(days=7 * i, hours=rng.randint(0, 3)),
                status="planned",
                seconds_before_live=0,
                live_started_at=None,
            )
            db.add(m)
            db.commit()
            db.refresh(m)

            lineup_rows = ensure_lineup(db, m, club_id)
            starters = [lu.player_id for lu in lineup_rows if lu.role == "starter"]
            bench = [lu.player_id for lu in lineup_rows if lu.role == "sub"]
            player_positions = build_player_position_map(db, starters + bench)
            match_profile = sample_match_profile(rng)
            plans = plan_substitutions(
                starters=starters,
                bench=bench,
                rng=rng,
                min_subs=2,
                max_subs=5,
                player_positions=player_positions,
                match_profile=match_profile,
            )
            create_substitutions(db, m, plans)

            generate_events(
                db,
                match=m,
                lineup_rows=lineup_rows,
                plans=plans,
                total_events=rng.randint(args.min_events, args.max_events),
                rng=rng,
                player_positions=player_positions,
                match_profile=match_profile,
            )
            created_ids.append(m.id)

        print("✅ Full match timelines generated")
        print(f"Club ID: {club_id}")
        print(f"Season ID: {season.id} ({season.name})")
        print(f"Deleted old matches: {deleted}")
        print(f"Generated matches: {len(created_ids)}")
        print(f"Match IDs: {created_ids[0]}..{created_ids[-1]}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
