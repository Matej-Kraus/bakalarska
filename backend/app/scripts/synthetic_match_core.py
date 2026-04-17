from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.match_event import MatchEvent
from app.models.match_lineup import MatchLineup
from app.models.match_player_rating import MatchPlayerRating
from app.models.match_player_stats import MatchPlayerStats
from app.models.match_substitution import MatchSubstitution
from app.models.player import Player
from app.models.season import Season
from app.models.season_player import SeasonPlayer
from app.services.stats_service import apply_event_to_match_stats
from app.util.time import utcnow

MAX_MATCH_SECOND = 90 * 60


@dataclass
class SubPlan:
    second_in_match: int
    half: int
    player_out_id: int
    player_in_id: int


def get_single_club_and_season(db: Session) -> tuple[int, Season]:
    season = db.query(Season).order_by(Season.id.asc()).first()
    if not season:
        raise RuntimeError("No season found. Run seed first.")
    return season.club_id, season


def delete_match_data(db: Session, match_id: int) -> None:
    db.query(MatchEvent).filter(MatchEvent.match_id == match_id).delete(synchronize_session=False)
    db.query(MatchPlayerStats).filter(MatchPlayerStats.match_id == match_id).delete(
        synchronize_session=False
    )
    db.query(MatchPlayerRating).filter(MatchPlayerRating.match_id == match_id).delete(
        synchronize_session=False
    )
    db.query(MatchSubstitution).filter(MatchSubstitution.match_id == match_id).delete(
        synchronize_session=False
    )
    db.query(MatchLineup).filter(MatchLineup.match_id == match_id).delete(synchronize_session=False)
    db.commit()


def ensure_lineup(db: Session, match: Match, club_id: int) -> list[MatchLineup]:
    existing = (
        db.query(MatchLineup)
        .filter(MatchLineup.match_id == match.id)
        .order_by(MatchLineup.id.asc())
        .all()
    )
    if existing:
        return existing

    players = (
        db.query(Player)
        .join(SeasonPlayer, SeasonPlayer.player_id == Player.id)
        .filter(Player.club_id == club_id, SeasonPlayer.season_id == match.season_id)
        .order_by(Player.jersey_number.asc())
        .all()
    )
    if len(players) < 12:
        raise RuntimeError("Need at least 12 players in season to generate a match")

    starters = players[:11]
    bench = players[11:16]

    rows: list[MatchLineup] = []
    for p in starters:
        row = MatchLineup(
            match_id=match.id,
            player_id=p.id,
            jersey_number_match=p.jersey_number,
            role="starter",
        )
        db.add(row)
        rows.append(row)
    for p in bench:
        row = MatchLineup(
            match_id=match.id,
            player_id=p.id,
            jersey_number_match=p.jersey_number,
            role="sub",
        )
        db.add(row)
        rows.append(row)

    db.commit()
    return (
        db.query(MatchLineup)
        .filter(MatchLineup.match_id == match.id)
        .order_by(MatchLineup.id.asc())
        .all()
    )


def plan_substitutions(
    *,
    starters: list[int],
    bench: list[int],
    rng: random.Random,
    min_subs: int = 2,
    max_subs: int = 5,
) -> list[SubPlan]:
    if not starters or not bench:
        return []

    subs_target = min(max_subs, len(bench), len(starters))
    subs_target = max(min_subs, subs_target)
    subs_target = min(subs_target, len(bench), len(starters))

    sub_minutes = sorted(rng.sample(range(53, 86), k=subs_target))
    out_candidates = starters[:]
    in_candidates = bench[:]
    rng.shuffle(out_candidates)
    rng.shuffle(in_candidates)

    plans: list[SubPlan] = []
    for i in range(subs_target):
        sec = sub_minutes[i] * 60 + rng.randint(0, 45)
        sec = max(1, min(sec, MAX_MATCH_SECOND))
        plans.append(
            SubPlan(
                second_in_match=sec,
                half=1 if sec < 45 * 60 else 2,
                player_out_id=out_candidates[i],
                player_in_id=in_candidates[i],
            )
        )

    return sorted(plans, key=lambda p: p.second_in_match)


def create_substitutions(db: Session, match: Match, plans: list[SubPlan]) -> None:
    for p in plans:
        db.add(
            MatchSubstitution(
                match_id=match.id,
                player_out_id=p.player_out_id,
                player_in_id=p.player_in_id,
                half=p.half,
                second_in_match=p.second_in_match,
            )
        )
    db.commit()


def generate_events(
    db: Session,
    match: Match,
    lineup_rows: list[MatchLineup],
    plans: list[SubPlan],
    total_events: int,
    rng: random.Random,
) -> None:
    starters = [r.player_id for r in lineup_rows if r.role == "starter"]
    bench = [r.player_id for r in lineup_rows if r.role == "sub"]
    on_field = set(starters)

    plans_sorted = sorted(plans, key=lambda p: p.second_in_match)
    plan_idx = 0

    weights = [
        ("pass", 38),
        ("won_duel", 10),
        ("lost_duel", 9),
        ("won_ball", 10),
        ("lost_ball", 9),
        ("foul", 6),
        ("shot_off_goal", 6),
        ("shot_on_goal", 5),
        ("assist", 2),
        ("goal", 2),
        ("error", 2),
        ("yellow_card", 1),
        ("penalty", 1),
    ]
    event_types = [x for x, _ in weights]
    event_weights = [w for _, w in weights]

    points = sorted(rng.randint(1, MAX_MATCH_SECOND) for _ in range(total_events))

    for second in points:
        while plan_idx < len(plans_sorted) and plans_sorted[plan_idx].second_in_match <= second:
            sub = plans_sorted[plan_idx]
            if sub.player_out_id in on_field:
                on_field.remove(sub.player_out_id)
            on_field.add(sub.player_in_id)
            plan_idx += 1

        if not on_field:
            # Fallback guard for malformed plans.
            on_field = set(starters if starters else bench)
            if not on_field:
                break

        player_id = rng.choice(list(on_field))
        event_type = rng.choices(event_types, weights=event_weights, k=1)[0]

        delta = 1
        if event_type == "pass" and rng.random() < 0.18:
            delta = -1

        half = 1 if second < 45 * 60 else 2
        ev = MatchEvent(
            match_id=match.id,
            player_id=player_id,
            event_type=event_type,
            delta=delta,
            half=half,
            second_in_match=second,
            created_at=utcnow(),
        )
        db.add(ev)
        apply_event_to_match_stats(
            db,
            match_id=match.id,
            player_id=player_id,
            event_type=event_type,
            delta=delta,
        )

        # Goals usually have an assist from another on-field teammate.
        if event_type == "goal" and delta > 0 and len(on_field) > 1 and rng.random() < 0.75:
            assist_candidates = [pid for pid in on_field if pid != player_id]
            assist_player = rng.choice(assist_candidates)
            assist_ev = MatchEvent(
                match_id=match.id,
                player_id=assist_player,
                event_type="assist",
                delta=1,
                half=half,
                second_in_match=min(MAX_MATCH_SECOND, second + rng.randint(0, 8)),
                created_at=utcnow(),
            )
            db.add(assist_ev)
            apply_event_to_match_stats(
                db,
                match_id=match.id,
                player_id=assist_player,
                event_type="assist",
                delta=1,
            )

        # Rare red card event.
        if rng.random() < 0.008:
            rc_player = rng.choice(list(on_field))
            rc_ev = MatchEvent(
                match_id=match.id,
                player_id=rc_player,
                event_type="red_card",
                delta=1,
                half=half,
                second_in_match=second,
                created_at=utcnow(),
            )
            db.add(rc_ev)
            apply_event_to_match_stats(
                db,
                match_id=match.id,
                player_id=rc_player,
                event_type="red_card",
                delta=1,
            )

    db.commit()

    match.status = "finished"
    match.live_started_at = None
    match.seconds_before_live = 90 * 60 + rng.randint(0, 180)
    db.commit()
"""
Shared helpers for generating synthetic match data (lineups, subs, events, stats).
Used by generate_analytics_test_match and generate_season_demo_data.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.club import Club
from app.models.match import Match
from app.models.match_event import MatchEvent
from app.models.match_lineup import MatchLineup
from app.models.match_player_rating import MatchPlayerRating
from app.models.match_player_stats import MatchPlayerStats
from app.models.match_substitution import MatchSubstitution
from app.models.player import Player
from app.models.season import Season
from app.services.stats_service import apply_event_to_match_stats


@dataclass
class SubPlan:
    player_out_id: int
    player_in_id: int
    second_in_match: int
    half: int


def get_single_club_and_season(db: Session) -> tuple[Club, Season]:
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


def delete_match_data(db: Session, match_id: int) -> None:
    """Delete events, stats, ratings, substitutions and lineup for a match."""
    db.query(MatchEvent).filter(MatchEvent.match_id == match_id).delete(
        synchronize_session=False
    )
    db.query(MatchSubstitution).filter(MatchSubstitution.match_id == match_id).delete(
        synchronize_session=False
    )
    db.query(MatchPlayerStats).filter(MatchPlayerStats.match_id == match_id).delete(
        synchronize_session=False
    )
    db.query(MatchPlayerRating).filter(MatchPlayerRating.match_id == match_id).delete(
        synchronize_session=False
    )
    db.query(MatchLineup).filter(MatchLineup.match_id == match_id).delete(
        synchronize_session=False
    )
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


def weighted_choice(rng: random.Random, items: list[tuple[str, int]]) -> str:
    total = sum(w for _, w in items)
    r = rng.uniform(0, total)
    upto = 0.0
    for value, weight in items:
        upto += weight
        if r <= upto:
            return value
    return items[-1][0]


def on_field_at_time(
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


def ensure_lineup(db: Session, match: Match, club: Club) -> list[MatchLineup]:
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

    for p in starters:
        db.add(
            MatchLineup(
                match_id=match.id,
                player_id=p.id,
                jersey_number_match=p.jersey_number,
                role="starter",
            )
        )
    for p in bench:
        db.add(
            MatchLineup(
                match_id=match.id,
                player_id=p.id,
                jersey_number_match=p.jersey_number,
                role="sub",
            )
        )
    db.commit()
    return (
        db.query(MatchLineup)
        .filter(MatchLineup.match_id == match.id)
        .order_by(MatchLineup.jersey_number_match.asc())
        .all()
    )


def plan_substitutions(
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
    out_ids = rng.sample(starters_list, num_subs)
    in_ids = rng.sample(bench_list, num_subs)
    sub_times: list[int] = sorted(rng.randint(50 * 60, 85 * 60) for _ in range(num_subs))

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


def create_substitutions(db: Session, match: Match, plans: list[SubPlan]) -> None:
    for plan in plans:
        db.add(
            MatchSubstitution(
                match_id=match.id,
                player_out_id=plan.player_out_id,
                player_in_id=plan.player_in_id,
                half=plan.half,
                second_in_match=plan.second_in_match,
            )
        )
    db.commit()


def generate_events(
    db: Session,
    match: Match,
    lineup_rows: list[MatchLineup],
    plans: list[SubPlan],
    total_events: int,
    rng: random.Random,
) -> None:
    """Generate events spread across full 90 minutes (0..5400 s) and update stats."""
    starter_ids = [lu.player_id for lu in lineup_rows if lu.role == "starter"]

    for _ in range(total_events):
        sec = rng.randint(0, 90 * 60)
        half = 1 if sec < 45 * 60 else 2
        on_field_ids = on_field_at_time(starter_ids, plans, sec)
        if not on_field_ids:
            continue
        player_id = rng.choice(on_field_ids)
        event_type = weighted_choice(rng, EVENT_WEIGHTS)
        delta = 1

        db.add(
            MatchEvent(
                match_id=match.id,
                player_id=player_id,
                event_type=event_type,
                delta=delta,
                half=half,
                second_in_match=sec,
            )
        )
        apply_event_to_match_stats(
            db,
            match_id=match.id,
            player_id=player_id,
            event_type=event_type,
            delta=delta,
        )

    db.commit()
