from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, distinct, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.match import Match
from app.models.match_event import MatchEvent
from app.models.match_player_rating import MatchPlayerRating
from app.models.match_player_stats import MatchPlayerStats
from app.models.player import Player
from app.models.season import Season
from app.models.user import User
from app.schemas.analytics import (
    LeaderboardRow,
    PlayerMatchPerformanceRow,
    TeamMatchBreakdownRow,
)
from app.schemas.stats import MatchPlayerStatsOut

router = APIRouter(tags=["analytics"])


@router.get("/players/{player_id}/performance", response_model=list[PlayerMatchPerformanceRow])
def player_performance(
    player_id: int,
    season_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    player = (
        db.query(Player)
        .filter(Player.id == player_id, Player.club_id == current_user.club_id)
        .first()
    )
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if season_id is not None:
        season = (
            db.query(Season)
            .filter(Season.id == season_id, Season.club_id == current_user.club_id)
            .first()
        )
        if not season:
            raise HTTPException(status_code=404, detail="Season not found")

    q = (
        db.query(Match, MatchPlayerStats, MatchPlayerRating)
        .join(MatchPlayerStats, MatchPlayerStats.match_id == Match.id)
        .outerjoin(
            MatchPlayerRating,
            (MatchPlayerRating.match_id == MatchPlayerStats.match_id)
            & (MatchPlayerRating.player_id == MatchPlayerStats.player_id),
        )
        .filter(
            MatchPlayerStats.player_id == player_id,
            Match.club_id == current_user.club_id,
        )
        .order_by(Match.match_date.asc(), Match.id.asc())
    )
    if season_id is not None:
        q = q.filter(Match.season_id == season_id)

    rows = q.all()

    match_ids = [m.id for (m, _s, _r) in rows]
    pass_map: dict[int, tuple[int, int]] = {}
    if match_ids:
        p_plus = func.sum(
            case(
                (and_(MatchEvent.event_type == "pass", MatchEvent.delta == 1), 1),
                else_=0,
            )
        )
        p_minus = func.sum(
            case(
                (and_(MatchEvent.event_type == "pass", MatchEvent.delta == -1), 1),
                else_=0,
            )
        )
        for mid, up, down in (
            db.query(MatchEvent.match_id, p_plus, p_minus)
            .filter(
                MatchEvent.player_id == player_id,
                MatchEvent.match_id.in_(match_ids),
            )
            .group_by(MatchEvent.match_id)
            .all()
        ):
            pass_map[int(mid)] = (int(up or 0), int(down or 0))

    resp: list[PlayerMatchPerformanceRow] = []
    for (m, s, r) in rows:
        ps, pu = pass_map.get(m.id, (0, 0))
        resp.append(
            PlayerMatchPerformanceRow(
                match_id=m.id,
                match_date=m.match_date,
                opponent=m.opponent,
                competition=m.competition,
                status=m.status,
                stats=MatchPlayerStatsOut.model_validate(s),
                rating=(r.rating if r else None),
                note=(r.note if r else None),
                passes_success=ps,
                passes_unsuccess=pu,
            )
        )
    return resp


@router.get("/seasons/{season_id}/leaderboards", response_model=list[LeaderboardRow])
def season_leaderboards(
    season_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    season = (
        db.query(Season)
        .filter(Season.id == season_id, Season.club_id == current_user.club_id)
        .first()
    )
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    q = (
        db.query(
            Player.id.label("player_id"),
            Player.first_name,
            Player.last_name,
            Player.jersey_number,
            func.count(distinct(MatchPlayerStats.match_id)).label("games"),
            func.sum(MatchPlayerStats.goals).label("goals"),
            func.sum(MatchPlayerStats.assists).label("assists"),
            func.sum(MatchPlayerStats.passes).label("passes"),
            func.sum(MatchPlayerStats.yellow_cards).label("yellow_cards"),
            func.sum(MatchPlayerStats.red_cards).label("red_cards"),
            func.avg(MatchPlayerRating.rating).label("avg_rating"),
        )
        .join(MatchPlayerStats, MatchPlayerStats.player_id == Player.id)
        .join(Match, Match.id == MatchPlayerStats.match_id)
        .outerjoin(
            MatchPlayerRating,
            (MatchPlayerRating.match_id == MatchPlayerStats.match_id)
            & (MatchPlayerRating.player_id == MatchPlayerStats.player_id),
        )
        .filter(
            Player.club_id == current_user.club_id,
            Match.club_id == current_user.club_id,
            Match.season_id == season_id,
        )
        .group_by(Player.id)
        .order_by(func.sum(MatchPlayerStats.goals).desc(), func.sum(MatchPlayerStats.assists).desc())
    )

    def z(x):
        return int(x or 0)

    resp: list[LeaderboardRow] = []
    for row in q.all():
        resp.append(
            LeaderboardRow(
                player_id=row.player_id,
                first_name=row.first_name,
                last_name=row.last_name,
                jersey_number=row.jersey_number,
                games=z(row.games),
                goals=z(row.goals),
                assists=z(row.assists),
                passes=z(row.passes),
                yellow_cards=z(row.yellow_cards),
                red_cards=z(row.red_cards),
                avg_rating=(float(row.avg_rating) if row.avg_rating is not None else None),
            )
        )
    return resp


@router.get(
    "/seasons/{season_id}/team-matches-breakdown",
    response_model=list[TeamMatchBreakdownRow],
)
def team_matches_breakdown(
    season_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Per-match aggregated team stats (sum over roster) for timeline charts."""
    season = (
        db.query(Season)
        .filter(Season.id == season_id, Season.club_id == current_user.club_id)
        .first()
    )
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    p_plus = func.sum(
        case(
            (and_(MatchEvent.event_type == "pass", MatchEvent.delta == 1), 1),
            else_=0,
        )
    )
    p_minus = func.sum(
        case(
            (and_(MatchEvent.event_type == "pass", MatchEvent.delta == -1), 1),
            else_=0,
        )
    )
    pass_subq = (
        db.query(
            MatchEvent.match_id.label("match_id"),
            p_plus.label("passes_success"),
            p_minus.label("passes_unsuccess"),
        )
        .join(Match, Match.id == MatchEvent.match_id)
        .filter(
            Match.season_id == season_id,
            Match.club_id == current_user.club_id,
        )
        .group_by(MatchEvent.match_id)
        .subquery()
    )

    rows = (
        db.query(
            Match.id.label("match_id"),
            Match.match_date,
            Match.opponent,
            Match.competition,
            Match.status,
            func.coalesce(func.sum(MatchPlayerStats.goals), 0).label("goals"),
            func.coalesce(func.sum(MatchPlayerStats.assists), 0).label("assists"),
            func.coalesce(func.sum(MatchPlayerStats.passes), 0).label("passes"),
            func.coalesce(pass_subq.c.passes_success, 0).label("passes_success"),
            func.coalesce(pass_subq.c.passes_unsuccess, 0).label("passes_unsuccess"),
            func.coalesce(func.sum(MatchPlayerStats.shots_on_goal), 0).label(
                "shots_on_goal"
            ),
            func.coalesce(func.sum(MatchPlayerStats.shots_off_goal), 0).label(
                "shots_off_goal"
            ),
            func.coalesce(func.sum(MatchPlayerStats.won_duels), 0).label("won_duels"),
            func.coalesce(func.sum(MatchPlayerStats.lost_duels), 0).label("lost_duels"),
            func.coalesce(func.sum(MatchPlayerStats.fouls), 0).label("fouls"),
            func.coalesce(func.sum(MatchPlayerStats.yellow_cards), 0).label(
                "yellow_cards"
            ),
            func.coalesce(func.sum(MatchPlayerStats.red_cards), 0).label("red_cards"),
        )
        .outerjoin(MatchPlayerStats, MatchPlayerStats.match_id == Match.id)
        .outerjoin(pass_subq, pass_subq.c.match_id == Match.id)
        .filter(Match.season_id == season_id, Match.club_id == current_user.club_id)
        .group_by(
            Match.id,
            pass_subq.c.passes_success,
            pass_subq.c.passes_unsuccess,
        )
        .order_by(Match.match_date.asc(), Match.id.asc())
        .all()
    )

    def zi(x) -> int:
        return int(x or 0)

    out: list[TeamMatchBreakdownRow] = []
    for row in rows:
        out.append(
            TeamMatchBreakdownRow(
                match_id=row.match_id,
                match_date=row.match_date,
                opponent=row.opponent,
                competition=row.competition,
                status=row.status,
                goals=zi(row.goals),
                assists=zi(row.assists),
                passes=zi(row.passes),
                passes_success=zi(row.passes_success),
                passes_unsuccess=zi(row.passes_unsuccess),
                shots_on_goal=zi(row.shots_on_goal),
                shots_off_goal=zi(row.shots_off_goal),
                won_duels=zi(row.won_duels),
                lost_duels=zi(row.lost_duels),
                fouls=zi(row.fouls),
                yellow_cards=zi(row.yellow_cards),
                red_cards=zi(row.red_cards),
            )
        )
    return out
