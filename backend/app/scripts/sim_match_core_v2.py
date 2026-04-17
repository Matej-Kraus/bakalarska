from __future__ import annotations

import random
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.match_event import MatchEvent
from app.models.match_lineup import MatchLineup
from app.models.match_player_rating import MatchPlayerRating
from app.models.match_player_stats import MatchPlayerStats
from app.models.match_substitution import MatchSubstitution
from app.models.player import Player
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
        raise RuntimeError("Need at least 12 players in season to generate matches")

    starters = players[:11]
    bench = players[11:16]
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

    sub_count = min(max_subs, len(bench), len(starters))
    sub_count = max(min_subs, sub_count)
    sub_count = min(sub_count, len(bench), len(starters))

    out_ids = starters[:]
    in_ids = bench[:]
    rng.shuffle(out_ids)
    rng.shuffle(in_ids)
    minutes = sorted(rng.sample(range(53, 86), k=sub_count))

    plans: list[SubPlan] = []
    for i in range(sub_count):
        sec = max(1, min(MAX_MATCH_SECOND, minutes[i] * 60 + rng.randint(0, 45)))
        plans.append(
            SubPlan(
                second_in_match=sec,
                half=1 if sec < 45 * 60 else 2,
                player_out_id=out_ids[i],
                player_in_id=in_ids[i],
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
    *,
    match: Match,
    lineup_rows: list[MatchLineup],
    plans: list[SubPlan],
    total_events: int,
    rng: random.Random,
) -> None:
    starters = [r.player_id for r in lineup_rows if r.role == "starter"]
    on_field = set(starters)
    plan_idx = 0
    plans = sorted(plans, key=lambda p: p.second_in_match)

    event_types = [
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
    kinds = [k for k, _ in event_types]
    weights = [w for _, w in event_types]
    seconds = sorted(rng.randint(1, MAX_MATCH_SECOND) for _ in range(total_events))

    for second in seconds:
        while plan_idx < len(plans) and plans[plan_idx].second_in_match <= second:
            sub = plans[plan_idx]
            if sub.player_out_id in on_field:
                on_field.remove(sub.player_out_id)
            on_field.add(sub.player_in_id)
            plan_idx += 1

        if not on_field:
            break

        player_id = rng.choice(list(on_field))
        event_type = rng.choices(kinds, weights=weights, k=1)[0]
        delta = -1 if event_type == "pass" and rng.random() < 0.18 else 1
        half = 1 if second < 45 * 60 else 2

        db.add(
            MatchEvent(
                match_id=match.id,
                player_id=player_id,
                event_type=event_type,
                delta=delta,
                half=half,
                second_in_match=second,
                created_at=utcnow(),
            )
        )
        apply_event_to_match_stats(db, match.id, player_id, event_type, delta)

        if event_type == "goal" and delta > 0 and len(on_field) > 1 and rng.random() < 0.75:
            assist_player = rng.choice([pid for pid in on_field if pid != player_id])
            assist_second = min(MAX_MATCH_SECOND, second + rng.randint(0, 8))
            db.add(
                MatchEvent(
                    match_id=match.id,
                    player_id=assist_player,
                    event_type="assist",
                    delta=1,
                    half=half,
                    second_in_match=assist_second,
                    created_at=utcnow(),
                )
            )
            apply_event_to_match_stats(db, match.id, assist_player, "assist", 1)

        if rng.random() < 0.008:
            rc_player = rng.choice(list(on_field))
            db.add(
                MatchEvent(
                    match_id=match.id,
                    player_id=rc_player,
                    event_type="red_card",
                    delta=1,
                    half=half,
                    second_in_match=second,
                    created_at=utcnow(),
                )
            )
            apply_event_to_match_stats(db, match.id, rc_player, "red_card", 1)

    db.commit()
    match.status = "finished"
    match.live_started_at = None
    match.seconds_before_live = 90 * 60 + rng.randint(0, 180)
    db.commit()
