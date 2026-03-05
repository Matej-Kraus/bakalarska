from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.models.match import Match
from app.models.season import Season
from app.models.user import User
from app.schemas.match import MatchCreate, MatchOut

router = APIRouter(prefix="/matches", tags=["matches"])

@router.post("", response_model=MatchOut)
def create_match(
    payload: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    # ověř season existuje
    season = (
        db.query(Season)
        .filter(Season.id == payload.season_id, Season.club_id == current_user.club_id)
        .first()
    )
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    # New matches are always created as planned; ignore payload.status for consistency
    m = Match(
        club_id=current_user.club_id,
        season_id=payload.season_id,
        opponent=payload.opponent,
        competition=payload.competition,
        match_date=payload.match_date,
        status="planned",
        seconds_before_live=0,
        live_started_at=None,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.get("", response_model=list[MatchOut])
def list_matches(
    season_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Match).filter(Match.club_id == current_user.club_id)
    if season_id is not None:
        q = q.filter(Match.season_id == season_id)
    return q.order_by(Match.match_date.desc()).all()

def _now_utc() -> datetime:
  # timezone-aware UTC to avoid ambiguity
  return datetime.now(timezone.utc)


@router.get("/{match_id}", response_model=MatchOut)
def get_match(
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
    return m


@router.post("/{match_id}/start", response_model=MatchOut)
def start_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    m = (
        db.query(Match)
        .filter(Match.id == match_id, Match.club_id == current_user.club_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    if m.status != "planned":
        raise HTTPException(status_code=400, detail="Match is not in planned state")

    m.status = "live_half_1"
    m.seconds_before_live = 0
    m.live_started_at = _now_utc()
    db.commit()
    db.refresh(m)
    return m


@router.post("/{match_id}/half-time", response_model=MatchOut)
def half_time(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    m = (
        db.query(Match)
        .filter(Match.id == match_id, Match.club_id == current_user.club_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    if m.status != "live_half_1":
        raise HTTPException(status_code=400, detail="Match is not in first half")
    if not m.live_started_at:
        raise HTTPException(status_code=400, detail="live_started_at not set")

    now = _now_utc()
    started = m.live_started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    elapsed = int((now - started).total_seconds())
    if elapsed < 0:
        elapsed = 0

    m.seconds_before_live += elapsed
    m.live_started_at = None
    m.status = "half_time"
    db.commit()
    db.refresh(m)
    return m


@router.post("/{match_id}/start-second-half", response_model=MatchOut)
def start_second_half(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    m = (
        db.query(Match)
        .filter(Match.id == match_id, Match.club_id == current_user.club_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    if m.status != "half_time":
        raise HTTPException(status_code=400, detail="Match is not in half-time")

    m.status = "live_half_2"
    m.live_started_at = _now_utc()
    db.commit()
    db.refresh(m)
    return m


@router.post("/{match_id}/finish", response_model=MatchOut)
def finish_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    m = (
        db.query(Match)
        .filter(Match.id == match_id, Match.club_id == current_user.club_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")

    if m.status in ("live_half_1", "live_half_2") and m.live_started_at:
        now = _now_utc()
        started = m.live_started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        elapsed = int((now - started).total_seconds())
        if elapsed < 0:
            elapsed = 0
        m.seconds_before_live += elapsed
        m.live_started_at = None

    m.status = "finished"
    db.commit()
    db.refresh(m)
    return m