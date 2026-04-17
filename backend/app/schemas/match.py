from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_serializer

MatchStatusLiteral = Literal["planned", "live_half_1", "half_time", "live_half_2", "finished"]


class MatchCreate(BaseModel):
    season_id: int
    opponent: str
    competition: str | None = None
    match_date: datetime
    status: MatchStatusLiteral = Field(default="planned")


class MatchOut(BaseModel):
    id: int
    season_id: int
    opponent: str
    competition: str | None = None
    match_date: datetime
    status: str
    seconds_before_live: int
    live_started_at: datetime | None = None

    @field_serializer("live_started_at")
    def serialize_live_started_at_utc(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")

    class Config:
        from_attributes = True
