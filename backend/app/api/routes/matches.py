from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.exceptions import AppError
from app.models.match import Match
from app.models.season import Season
from app.models.user import User
from app.schemas.match import MatchCreate, MatchOut
from app.services.match_service import (
    delete_match,
    finish_match,
    get_match_or_404,
    half_time,
    start_match,
    start_second_half,
)

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("", response_model=MatchOut)
def create_match(
    payload: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    season = (
        db.query(Season)
        .filter(Season.id == payload.season_id, Season.club_id == current_user.club_id)
        .first()
    )
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

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


@router.get("/{match_id}", response_model=MatchOut)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        m = get_match_or_404(db, match_id, current_user.club_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return m


@router.post("/{match_id}/start", response_model=MatchOut)
def start_match_route(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    try:
        return start_match(db, match_id, current_user.club_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{match_id}/half-time", response_model=MatchOut)
def half_time_route(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    try:
        return half_time(db, match_id, current_user.club_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{match_id}/start-second-half", response_model=MatchOut)
def start_second_half_route(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    try:
        return start_second_half(db, match_id, current_user.club_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{match_id}/finish", response_model=MatchOut)
def finish_match_route(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    try:
        return finish_match(db, match_id, current_user.club_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/{match_id}", status_code=204)
def delete_match_route(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    try:
        delete_match(db, match_id, current_user.club_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
