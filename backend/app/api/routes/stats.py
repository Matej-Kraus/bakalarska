from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.api.deps import get_current_user, get_db
from app.models.match import Match
from app.models.player import Player
from app.models.match_lineup import MatchLineup
from app.models.match_player_stats import MatchPlayerStats
from app.models.user import User
from app.schemas.stats import MatchPlayerStatsOut

router = APIRouter(prefix="/matches", tags=["stats"])


@router.get("/{match_id}/stats", response_model=list[MatchPlayerStatsOut])
def get_match_stats(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = (
        db.query(Match)
        .filter(Match.id == match_id, Match.club_id == current_user.club_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")

    return (
        db.query(MatchPlayerStats)
        .filter(MatchPlayerStats.match_id == match_id)
        .order_by(MatchPlayerStats.player_id.asc())
        .all()
    )


@router.get("/{match_id}/roster-with-stats")
def get_roster_with_stats(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns nominated players (starter/sub), sorted by jersey number for match,
    and attaches their aggregated match stats (default zeros if no stats yet).
    """
    m = (
        db.query(Match)
        .filter(Match.id == match_id, Match.club_id == current_user.club_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")

    rows = (
        db.query(MatchLineup, Player, MatchPlayerStats)
        .join(Player, Player.id == MatchLineup.player_id)
        .outerjoin(
            MatchPlayerStats,
            (MatchPlayerStats.match_id == MatchLineup.match_id)
            & (MatchPlayerStats.player_id == MatchLineup.player_id),
        )
        .filter(MatchLineup.match_id == match_id, Player.club_id == current_user.club_id)
        .order_by(asc(MatchLineup.jersey_number_match))
        .all()
    )

    def stats_dict(s: MatchPlayerStats | None) -> dict:
        # pokud ještě hráč nemá žádný event, tak stats řádek neexistuje => vrať nuly
        if not s:
            return {
                "goals": 0,
                "assists": 0,
                "errors": 0,
                "won_balls": 0,
                "lost_balls": 0,
                "fouls": 0,
                "passes": 0,
                "won_duels": 0,
                "lost_duels": 0,
                "shots_on_goal": 0,
                "shots_off_goal": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "penalties": 0,
            }

        return {
            "goals": s.goals,
            "assists": s.assists,
            "errors": s.errors,
            "won_balls": s.won_balls,
            "lost_balls": s.lost_balls,
            "fouls": s.fouls,
            "passes": s.passes,
            "won_duels": s.won_duels,
            "lost_duels": s.lost_duels,
            "shots_on_goal": s.shots_on_goal,
            "shots_off_goal": s.shots_off_goal,
            "yellow_cards": s.yellow_cards,
            "red_cards": s.red_cards,
            "penalties": s.penalties,
        }

    return [
        {
            "player_id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "role": lu.role,
            "jersey_number_match": lu.jersey_number_match,
            "stats": stats_dict(s),
        }
        for (lu, p, s) in rows
    ]