from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
import random
from typing import Iterable

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.club import Club
from app.models.season import Season
from app.models.match import Match
from app.models.player import Player
from app.models.match_lineup import MatchLineup
from app.models.match_event import MatchEvent
from app.models.match_substitution import MatchSubstitution
from app.models.match_player_stats import MatchPlayerStats
from app.models.match_player_rating import MatchPlayerRating
from app.services.stats_service import apply_event_to_match_stats


TEST_MATCH_OPPONENT_DEFAULT = "Analytics Test Match"


@dataclass
class SubPlan:
  player_out_id: int
  player_in_id: int
  second_in_match: int
  half: int


def _get_single_club_and_season(db: Session) -> tuple[Club, Season]:
  club = db.query(Club).order_by(Club.id.asc()).first()
  if not club:
    raise RuntimeError("No clubs found in database. Run seed.py first.")

  season = (
    db.query(Season)
    .filter(Season.club_id == club.id)
    .order_by(Season.id.asc())
    .first()
  )
  if not season:
    raise RuntimeError("No seasons found for club. Run seed.py first.")

  return club, season


def _delete_match_data(db: Session, match_id: int) -> None:
  """Delete events, stats, ratings, substitutions and lineup for a match."""
  db.query(MatchEvent).filter(MatchEvent.match_id == match_id).delete(
    synchronize_session=False
  )
  db.query(MatchSubstitution).filter(
    MatchSubstitution.match_id == match_id
  ).delete(synchronize_session=False)
  db.query(MatchPlayerStats).filter(
    MatchPlayerStats.match_id == match_id
  ).delete(synchronize_session=False)
  db.query(MatchPlayerRating).filter(
    MatchPlayerRating.match_id == match_id
  ).delete(synchronize_session=False)
  db.query(MatchLineup).filter(MatchLineup.match_id == match_id).delete(
    synchronize_session=False
  )
  db.commit()


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
    _delete_match_data(db, existing.id)
    db.delete(existing)
    db.commit()

  # Use "finished" so evaluation/analytics screens are available.
  match = Match(
    club_id=club.id,
    season_id=season.id,
    opponent=opponent_name,
    competition="Analytics Test",
    match_date=datetime.utcnow(),
    status="finished",
    # 90 minutes played (seconds) – timer model uses seconds_before_live when finished.
    seconds_before_live=90 * 60,
    live_started_at=None,
  )
  db.add(match)
  db.commit()
  db.refresh(match)
  return match


def _ensure_lineup(db: Session, match: Match, club: Club) -> list[MatchLineup]:
  """Ensure the match has a full lineup (11 starters + bench)."""
  existing = (
    db.query(MatchLineup)
    .filter(MatchLineup.match_id == match.id)
    .order_by(MatchLineup.jersey_number_match.asc())
    .all()
  )
  if existing:
    return existing

  players: list[Player] = (
    db.query(Player)
    .filter(Player.club_id == club.id)
    .order_by(Player.jersey_number.asc())
    .all()
  )
  if len(players) < 11:
    raise RuntimeError("Need at least 11 players to create lineup.")

  starters = players[:11]
  bench = players[11:]

  lineup_rows: list[MatchLineup] = []

  for p in starters:
    lu = MatchLineup(
      match_id=match.id,
      player_id=p.id,
      jersey_number_match=p.jersey_number,
      role="starter",
    )
    db.add(lu)
    lineup_rows.append(lu)

  for p in bench:
    lu = MatchLineup(
      match_id=match.id,
      player_id=p.id,
      jersey_number_match=p.jersey_number,
      role="sub",
    )
    db.add(lu)
    lineup_rows.append(lu)

  db.commit()
  # Reload with IDs populated
  return (
    db.query(MatchLineup)
    .filter(MatchLineup.match_id == match.id)
    .order_by(MatchLineup.jersey_number_match.asc())
    .all()
  )


def _plan_substitutions(
  starters: Iterable[int],
  bench: Iterable[int],
  rng: random.Random,
  min_subs: int = 2,
  max_subs: int = 4,
) -> list[SubPlan]:
  starters_list = list(starters)
  bench_list = list(bench)
  if not starters_list or not bench_list:
    return []

  num_subs = min(max_subs, max(min_subs, min(len(starters_list), len(bench_list))))
  # Choose distinct starters to substitute out.
  out_ids = rng.sample(starters_list, num_subs)
  in_ids = rng.sample(bench_list, num_subs)

  # Substitutions in the second half, between 50th and 85th minute.
  sub_times: list[int] = sorted(
    rng.randint(50 * 60, 85 * 60) for _ in range(num_subs)
  )

  plans: list[SubPlan] = []
  for out_id, in_id, sec in zip(out_ids, in_ids, sub_times):
    half = 1 if sec < 45 * 60 else 2
    plans.append(
      SubPlan(
        player_out_id=out_id,
        player_in_id=in_id,
        second_in_match=sec,
        half=half,
      )
    )
  return plans


def _create_substitutions(
  db: Session, match: Match, plans: list[SubPlan]
) -> None:
  for plan in plans:
    sub = MatchSubstitution(
      match_id=match.id,
      player_out_id=plan.player_out_id,
      player_in_id=plan.player_in_id,
      half=plan.half,
      second_in_match=plan.second_in_match,
    )
    db.add(sub)
  db.commit()


EVENT_WEIGHTS: list[tuple[str, int]] = [
  ("pass", 60),
  ("won_duel", 15),
  ("lost_duel", 15),
  ("shot_on_goal", 4),
  ("shot_off_goal", 6),
  ("foul", 6),
  ("goal", 2),
  ("yellow_card", 2),
  ("red_card", 1),
  ("penalty", 1),
]


def _weighted_choice(rng: random.Random, items: list[tuple[str, int]]) -> str:
  total = sum(w for _, w in items)
  r = rng.uniform(0, total)
  upto = 0.0
  for value, weight in items:
    upto += weight
    if r <= upto:
      return value
  # Fallback – should not happen
  return items[-1][0]


def _on_field_at_time(
  starters: Iterable[int],
  plans: list[SubPlan],
  second_in_match: int,
) -> list[int]:
  on_field = set(starters)
  for plan in plans:
    if plan.second_in_match <= second_in_match:
      if plan.player_out_id in on_field:
        on_field.remove(plan.player_out_id)
      on_field.add(plan.player_in_id)
  return list(on_field)


def _generate_events(
  db: Session,
  match: Match,
  lineup_rows: list[MatchLineup],
  plans: list[SubPlan],
  total_events: int,
  rng: random.Random,
) -> None:
  # Starter IDs drive initial on-field list.
  starter_ids = [lu.player_id for lu in lineup_rows if lu.role == "starter"]

  for _ in range(total_events):
    # Full match: 0–5400 seconds (90 minutes).
    sec = rng.randint(0, 90 * 60)
    half = 1 if sec < 45 * 60 else 2

    on_field_ids = _on_field_at_time(starter_ids, plans, sec)
    if not on_field_ids:
      continue
    player_id = rng.choice(on_field_ids)

    event_type = _weighted_choice(rng, EVENT_WEIGHTS)
    delta = 1  # only positive events; UI "undo" (-1) not needed for synthetic data

    ev = MatchEvent(
      match_id=match.id,
      player_id=player_id,
      event_type=event_type,
      delta=delta,
      half=half,
      second_in_match=sec,
    )
    db.add(ev)

    # Keep aggregated stats in sync with events.
    apply_event_to_match_stats(
      db,
      match_id=match.id,
      player_id=player_id,
      event_type=event_type,
      delta=delta,
    )

  db.commit()


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
    club, season = _get_single_club_and_season(db)
    match = _get_or_create_test_match(
      db,
      club=club,
      season=season,
      opponent_name=args.opponent_name,
      replace_existing=bool(args.replace_existing),
    )
    lineup_rows = _ensure_lineup(db, match, club)

    starter_ids = [lu.player_id for lu in lineup_rows if lu.role == "starter"]
    bench_ids = [lu.player_id for lu in lineup_rows if lu.role == "sub"]

    plans = _plan_substitutions(
      starters=starter_ids,
      bench=bench_ids,
      rng=rng,
      min_subs=2,
      max_subs=4,
    )
    _create_substitutions(db, match, plans)

    total_events = max(300, args.events)
    _generate_events(db, match, lineup_rows, plans, total_events, rng)

    events_count = db.query(MatchEvent).filter(MatchEvent.match_id == match.id).count()
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

