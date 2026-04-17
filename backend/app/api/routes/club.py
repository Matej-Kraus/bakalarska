from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.models.club import Club
from app.models.user import User
from app.schemas.club import ClubOut, ClubUpdate

router = APIRouter(prefix="/club", tags=["club"])


@router.get("", response_model=ClubOut)
def get_my_club(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    club = db.get(Club, current_user.club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


@router.put("", response_model=ClubOut)
def update_my_club(
    payload: ClubUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    club = db.get(Club, current_user.club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Unique name: another club must not already use this name
    existing = (
        db.query(Club)
        .filter(Club.name == payload.name, Club.id != club.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A club with this name already exists",
        )

    club.name = payload.name.strip()
    club.short_name = payload.short_name.strip() if payload.short_name else None
    club.city = payload.city.strip() if payload.city else None
    club.home_venue = payload.home_venue.strip() if payload.home_venue else None
    club.founded_year = payload.founded_year

    db.commit()
    db.refresh(club)
    return club
