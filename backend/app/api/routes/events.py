from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.match import Match
from app.models.match_event import MatchEvent
from app.models.match_lineup import MatchLineup
from app.models.player import Player
from app.models.user import User
from app.schemas.event import MatchEventCreate, MatchEventOut, ALLOWED_EVENT_TYPES
from app.services.stats_service import apply_event_to_match_stats

router = APIRouter(prefix="/matches", tags=["events"])


@router.post("/{match_id}/events", response_model=MatchEventOut)
def add_match_event(
    match_id: int,
    payload: MatchEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # basic validation
    if payload.event_type not in ALLOWED_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported event_type")
    if payload.delta not in (-1, 1):
        raise HTTPException(status_code=400, detail="delta must be -1 or +1")
    if payload.half not in (1, 2):
        raise HTTPException(status_code=400, detail="half must be 1 or 2")

    # match must exist and be live
    m = (
        db.query(Match)
        .filter(Match.id == match_id, Match.club_id == current_user.club_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    if m.status not in ("live_half_1", "live_half_2"):
        raise HTTPException(status_code=400, detail="Match is not live")

    # player must be in lineup (starter or sub)
    in_lineup = (
        db.query(MatchLineup.id)
        .join(Player, Player.id == MatchLineup.player_id)
        .filter(MatchLineup.match_id == match_id, MatchLineup.player_id == payload.player_id)
        .filter(Player.club_id == current_user.club_id)
        .first()
    )
    if not in_lineup:
        raise HTTPException(status_code=400, detail="Player is not in lineup for this match")

    # 1) create event
    ev = MatchEvent(
        match_id=match_id,
        player_id=payload.player_id,
        event_type=payload.event_type,
        delta=payload.delta,
        half=payload.half,
        second_in_match=payload.second_in_match,
    )
    db.add(ev)

    # 2) update aggregated stats (same transaction)
    try:
        apply_event_to_match_stats(
            db,
            match_id=match_id,
            player_id=payload.player_id,
            event_type=payload.event_type,
            delta=payload.delta,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.commit()
    db.refresh(ev)
    return ev


@router.get("/{match_id}/events", response_model=list[MatchEventOut])
def list_match_events(
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
        db.query(MatchEvent)
        .filter(MatchEvent.match_id == match_id)
        .order_by(MatchEvent.second_in_match.asc(), MatchEvent.id.asc())
        .all()
    )