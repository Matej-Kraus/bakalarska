from datetime import timedelta

from jose import JWTError, jwt

from app.core.settings import settings
from app.util.time import utcnow


def create_access_token(*, user_id: int, club_id: int, role: str) -> str:
    now = utcnow()
    exp = now + timedelta(minutes=settings.access_token_exp_minutes)
    payload = {
        "sub": str(user_id),
        "club_id": club_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": exp,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError("Invalid token") from e

