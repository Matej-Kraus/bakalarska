from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.match import Match
from app.models.match_player_rating import MatchPlayerRating
from app.models.match_player_stats import MatchPlayerStats
from app.models.player import Player
from app.models.season import Season
from app.models.user import User
from app.schemas.analytics import LeaderboardRow, PlayerMatchPerformanceRow
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

    resp: list[PlayerMatchPerformanceRow] = []
    for (m, s, r) in rows:
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
            func.count(MatchPlayerStats.id).label("games"),
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

