from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.club import Club
from app.models.season import Season
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterOut, RegisterRequest, TokenOut, UserOut
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _default_season_name() -> str:
    year = datetime.now().year
    return f"{year}/{year + 1}"


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user_id=user.id, club_id=user.club_id, role=user.role)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.post("/register", response_model=TokenOut)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    club_name = payload.club_name.strip()
    password = payload.password
    role = payload.role

    if not club_name:
        raise HTTPException(status_code=400, detail="Club name is required")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must have at least 6 characters")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User with this email already exists")

    existing_club = db.query(Club).filter(Club.name == club_name).first()
    if existing_club:
        raise HTTPException(status_code=409, detail="Club with this name already exists")

    club = Club(name=club_name)
    db.add(club)
    db.flush()

    user = User(
        club_id=club.id,
        email=email,
        password_hash=hash_password(password),
        role=role,
        email_verified=True,
        email_verification_token=None,
    )
    db.add(user)

    season = Season(club_id=club.id, name=_default_season_name())
    db.add(season)

    db.commit()
    db.refresh(user)
    token = create_access_token(user_id=user.id, club_id=user.club_id, role=user.role)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/verify-email", response_model=RegisterOut)
def verify_email(token: str = Query(..., min_length=16), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    user.email_verified = True
    user.email_verification_token = None
    db.commit()
    return RegisterOut(message="Email verified successfully. You can now login.")

