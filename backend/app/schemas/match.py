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


class SeasonGenerationRequest(BaseModel):
    season_id: int
    matches: int = Field(default=20, ge=1, le=200)
    seed: int = Field(default=2026)
    replace_existing: bool = Field(default=True)
    min_events: int = Field(default=520, ge=1)
    max_events: int = Field(default=820, ge=1)


class SeasonGenerationOut(BaseModel):
    season_id: int
    deleted_old_matches: int
    generated_matches: int
    first_match_id: int | None = None
    last_match_id: int | None = None


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
