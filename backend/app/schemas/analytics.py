from datetime import datetime

from pydantic import BaseModel

from app.schemas.stats import MatchPlayerStatsOut


class PlayerMatchPerformanceRow(BaseModel):
    match_id: int
    match_date: datetime
    opponent: str
    competition: str | None
    status: str
    stats: MatchPlayerStatsOut
    rating: int | None = None
    note: str | None = None


class LeaderboardRow(BaseModel):
    player_id: int
    first_name: str
    last_name: str
    jersey_number: int
    games: int
    goals: int
    assists: int
    passes: int
    yellow_cards: int
    red_cards: int
    avg_rating: float | None = None

