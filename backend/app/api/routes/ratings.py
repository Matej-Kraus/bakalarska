from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.models.match import Match
from app.models.match_lineup import MatchLineup
from app.models.match_player_rating import MatchPlayerRating
from app.models.player import Player
from app.models.user import User
from app.schemas.rating import RatingOut, RatingsSaveRequest

router = APIRouter(prefix="/matches", tags=["ratings"])


@router.get("/{match_id}/ratings", response_model=list[RatingOut])
def list_ratings(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.club_id == current_user.club_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    return (
        db.query(MatchPlayerRating)
        .filter(MatchPlayerRating.match_id == match_id)
        .order_by(MatchPlayerRating.player_id.asc())
        .all()
    )


@router.put("/{match_id}/ratings", response_model=list[RatingOut])
def save_ratings(
    match_id: int,
    payload: RatingsSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coach")),
):
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.club_id == current_user.club_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status != "finished":
        raise HTTPException(
            status_code=400,
            detail="Ratings can only be saved after the match is finished",
        )

    # Validate: each player must be nominated in lineup for this match and belong to club.
    nominated_ids = {
        pid
        for (pid,) in (
            db.query(MatchLineup.player_id)
            .join(Player, Player.id == MatchLineup.player_id)
            .filter(MatchLineup.match_id == match_id, Player.club_id == current_user.club_id)
            .all()
        )
    }
    missing = [i.player_id for i in payload.items if i.player_id not in nominated_ids]
    if missing:
        raise HTTPException(status_code=400, detail=f"Players not in lineup: {missing}")

    # Replace existing ratings for match (MVP simplicity).
    db.query(MatchPlayerRating).filter(MatchPlayerRating.match_id == match_id).delete()

    rows: list[MatchPlayerRating] = []
    for item in payload.items:
        r = MatchPlayerRating(
            match_id=match_id,
            player_id=item.player_id,
            user_id=current_user.id,
            rating=item.rating,
            note=item.note,
        )
        db.add(r)
        rows.append(r)

    db.commit()
    for r in rows:
        db.refresh(r)
    return rows

