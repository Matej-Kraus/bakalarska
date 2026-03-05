from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.api.deps import get_current_user, get_db
from app.models.match import Match
from app.models.player import Player
from app.models.season import Season
from app.models.match_player_stats import MatchPlayerStats
from app.models.user import User
from app.schemas.report import StatsSumOut

router = APIRouter(tags=["reports"])


def _sum_stats(q) -> StatsSumOut:
    row = q.one()

    # row = (games, goals, assists, ...)
    # pokud není nic, SUM vrací None => převedeme na 0
    def z(x):
        return int(x or 0)

    return StatsSumOut(
        games=z(row.games),
        goals=z(row.goals),
        assists=z(row.assists),
        errors=z(row.errors),
        won_balls=z(row.won_balls),
        lost_balls=z(row.lost_balls),
        fouls=z(row.fouls),
        passes=z(row.passes),
        won_duels=z(row.won_duels),
        lost_duels=z(row.lost_duels),
        shots_on_goal=z(row.shots_on_goal),
        shots_off_goal=z(row.shots_off_goal),
        yellow_cards=z(row.yellow_cards),
        red_cards=z(row.red_cards),
        penalties=z(row.penalties),
    )


@router.get("/players/{player_id}/stats/season/{season_id}", response_model=StatsSumOut)
def player_stats_season(
    player_id: int,
    season_id: int,
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
    season = (
        db.query(Season)
        .filter(Season.id == season_id, Season.club_id == current_user.club_id)
        .first()
    )
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    q = (
        db.query(
            func.count(MatchPlayerStats.id).label("games"),
            func.sum(MatchPlayerStats.goals).label("goals"),
            func.sum(MatchPlayerStats.assists).label("assists"),
            func.sum(MatchPlayerStats.errors).label("errors"),
            func.sum(MatchPlayerStats.won_balls).label("won_balls"),
            func.sum(MatchPlayerStats.lost_balls).label("lost_balls"),
            func.sum(MatchPlayerStats.fouls).label("fouls"),
            func.sum(MatchPlayerStats.passes).label("passes"),
            func.sum(MatchPlayerStats.won_duels).label("won_duels"),
            func.sum(MatchPlayerStats.lost_duels).label("lost_duels"),
            func.sum(MatchPlayerStats.shots_on_goal).label("shots_on_goal"),
            func.sum(MatchPlayerStats.shots_off_goal).label("shots_off_goal"),
            func.sum(MatchPlayerStats.yellow_cards).label("yellow_cards"),
            func.sum(MatchPlayerStats.red_cards).label("red_cards"),
            func.sum(MatchPlayerStats.penalties).label("penalties"),
        )
        .join(Match, Match.id == MatchPlayerStats.match_id)
        .filter(
            MatchPlayerStats.player_id == player_id,
            Match.season_id == season_id,
            Match.club_id == current_user.club_id,
        )
    )
    return _sum_stats(q)


@router.get("/players/{player_id}/stats/last/{n}", response_model=StatsSumOut)
def player_stats_last_n(
    player_id: int,
    n: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if n <= 0 or n > 200:
        raise HTTPException(status_code=400, detail="n must be between 1 and 200")
    player = (
        db.query(Player)
        .filter(Player.id == player_id, Player.club_id == current_user.club_id)
        .first()
    )
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # nejdřív vyber posledních N match_id kde hráč má stats
    last_match_ids = (
        db.query(MatchPlayerStats.match_id)
        .join(Match, Match.id == MatchPlayerStats.match_id)
        .filter(MatchPlayerStats.player_id == player_id, Match.club_id == current_user.club_id)
        .order_by(desc(Match.match_date), desc(Match.id))
        .limit(n)
        .all()
    )
    match_ids = [x[0] for x in last_match_ids]
    if not match_ids:
        # žádné zápasy -> nuly
        return StatsSumOut(
            games=0, goals=0, assists=0, errors=0, won_balls=0, lost_balls=0, fouls=0,
            passes=0, won_duels=0, lost_duels=0, shots_on_goal=0, shots_off_goal=0,
            yellow_cards=0, red_cards=0, penalties=0
        )

    q = (
        db.query(
            func.count(MatchPlayerStats.id).label("games"),
            func.sum(MatchPlayerStats.goals).label("goals"),
            func.sum(MatchPlayerStats.assists).label("assists"),
            func.sum(MatchPlayerStats.errors).label("errors"),
            func.sum(MatchPlayerStats.won_balls).label("won_balls"),
            func.sum(MatchPlayerStats.lost_balls).label("lost_balls"),
            func.sum(MatchPlayerStats.fouls).label("fouls"),
            func.sum(MatchPlayerStats.passes).label("passes"),
            func.sum(MatchPlayerStats.won_duels).label("won_duels"),
            func.sum(MatchPlayerStats.lost_duels).label("lost_duels"),
            func.sum(MatchPlayerStats.shots_on_goal).label("shots_on_goal"),
            func.sum(MatchPlayerStats.shots_off_goal).label("shots_off_goal"),
            func.sum(MatchPlayerStats.yellow_cards).label("yellow_cards"),
            func.sum(MatchPlayerStats.red_cards).label("red_cards"),
            func.sum(MatchPlayerStats.penalties).label("penalties"),
        )
        .filter(
            MatchPlayerStats.player_id == player_id,
            MatchPlayerStats.match_id.in_(match_ids),
        )
    )
    return _sum_stats(q)


@router.get("/seasons/{season_id}/team-stats", response_model=StatsSumOut)
def team_stats_season(
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
            func.count(MatchPlayerStats.id).label("games"),
            func.sum(MatchPlayerStats.goals).label("goals"),
            func.sum(MatchPlayerStats.assists).label("assists"),
            func.sum(MatchPlayerStats.errors).label("errors"),
            func.sum(MatchPlayerStats.won_balls).label("won_balls"),
            func.sum(MatchPlayerStats.lost_balls).label("lost_balls"),
            func.sum(MatchPlayerStats.fouls).label("fouls"),
            func.sum(MatchPlayerStats.passes).label("passes"),
            func.sum(MatchPlayerStats.won_duels).label("won_duels"),
            func.sum(MatchPlayerStats.lost_duels).label("lost_duels"),
            func.sum(MatchPlayerStats.shots_on_goal).label("shots_on_goal"),
            func.sum(MatchPlayerStats.shots_off_goal).label("shots_off_goal"),
            func.sum(MatchPlayerStats.yellow_cards).label("yellow_cards"),
            func.sum(MatchPlayerStats.red_cards).label("red_cards"),
            func.sum(MatchPlayerStats.penalties).label("penalties"),
        )
        .join(Match, Match.id == MatchPlayerStats.match_id)
        .filter(Match.season_id == season_id, Match.club_id == current_user.club_id)
    )
    return _sum_stats(q)