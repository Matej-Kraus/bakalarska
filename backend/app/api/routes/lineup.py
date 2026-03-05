from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.api.deps import get_current_user, get_db, require_role
from app.models.player import Player
from app.models.match import Match
from app.models.match_lineup import MatchLineup
from app.models.user import User
from app.schemas.lineup import LineupSaveRequest, LineupEditorResponse, LineupEditorPlayer

router = APIRouter(prefix="/matches", tags=["lineup"])

VALID_ROLES = {"starter", "sub"}


@router.get("/{match_id}/lineup-editor", response_model=LineupEditorResponse)
def get_lineup_editor(
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

    players = (
        db.query(Player)
        .filter(Player.club_id == current_user.club_id)
        .order_by(Player.jersey_number)
        .all()
    )
    lineup_rows = db.query(MatchLineup).filter(MatchLineup.match_id == match_id).all()

    lineup_by_player = {r.player_id: r for r in lineup_rows}
    taken_numbers = sorted([r.jersey_number_match for r in lineup_rows])

    resp_players: list[LineupEditorPlayer] = []
    for p in players:
        lr = lineup_by_player.get(p.id)
        if lr:
            role = lr.role
            jersey = lr.jersey_number_match
        else:
            role = "out"
            jersey = None

        resp_players.append(
            LineupEditorPlayer(
                player_id=p.id,
                first_name=p.first_name,
                last_name=p.last_name,
                default_jersey_number=p.jersey_number,
                role=role,
                jersey_number_match=jersey,
            )
        )

    return LineupEditorResponse(
        match_id=match_id,
        taken_numbers=taken_numbers,
        players=resp_players,
    )


@router.put("/{match_id}/lineup")
def save_lineup(
    match_id: int,
    payload: LineupSaveRequest,
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

    # validate roles + duplicates
    seen_players: set[int] = set()
    seen_numbers: set[int] = set()

    starters = 0
    subs = 0

    for item in payload.items:
        if item.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"Invalid role: {item.role}")

        if item.player_id in seen_players:
            raise HTTPException(status_code=400, detail="Duplicate player in lineup")
        seen_players.add(item.player_id)

        if item.jersey_number_match in seen_numbers:
            raise HTTPException(status_code=400, detail="Duplicate jersey_number_match in lineup")
        seen_numbers.add(item.jersey_number_match)

        if item.role == "starter":
            starters += 1
        else:
            subs += 1

    # optional strict limits
    if starters > 11:
        raise HTTPException(status_code=400, detail="Too many starters (max 11)")
    if subs > 5:
        raise HTTPException(status_code=400, detail="Too many subs (max 5)")

    # ensure players exist
    ids = [i.player_id for i in payload.items]
    if ids:
        existing = (
            db.query(Player.id)
            .filter(Player.club_id == current_user.club_id, Player.id.in_(ids))
            .all()
        )
        existing_ids = {x[0] for x in existing}
        missing = [pid for pid in ids if pid not in existing_ids]
        if missing:
            raise HTTPException(status_code=400, detail=f"Players not found: {missing}")

    # replace lineup (simple + clean)
    db.query(MatchLineup).filter(MatchLineup.match_id == match_id).delete()
    for item in payload.items:
        db.add(
            MatchLineup(
                match_id=match_id,
                player_id=item.player_id,
                jersey_number_match=item.jersey_number_match,
                role=item.role,
            )
        )
    db.commit()

    return {"ok": True, "match_id": match_id, "starters": starters, "subs": subs}


@router.get("/{match_id}/roster")
def get_roster(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns only nominated players (starter/sub), sorted by jersey number for match.
    Perfect for live match UI.
    """
    m = (
        db.query(Match)
        .filter(Match.id == match_id, Match.club_id == current_user.club_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")

    rows = (
        db.query(MatchLineup, Player)
        .join(Player, Player.id == MatchLineup.player_id)
        .filter(MatchLineup.match_id == match_id, Player.club_id == current_user.club_id)
        .order_by(asc(MatchLineup.jersey_number_match))
        .all()
    )

    return [
        {
            "player_id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "jersey_number_match": lu.jersey_number_match,
            "role": lu.role,
        }
        for (lu, p) in rows
    ]