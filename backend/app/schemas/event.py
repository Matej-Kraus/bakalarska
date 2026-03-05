from pydantic import BaseModel, Field


ALLOWED_EVENT_TYPES = {
    "goal",
    "assist",
    "error",
    "won_ball",
    "lost_ball",
    "foul",
    "pass",
    "won_duel",
    "lost_duel",
    "shot_on_goal",
    "shot_off_goal",
    "yellow_card",
    "red_card",
    "penalty",
}


class MatchEventCreate(BaseModel):
    """Event recorded during a live match. second_in_match = total seconds into the match (0 = kick-off 1st half)."""

    player_id: int
    event_type: str
    delta: int = Field(..., description="Use +1 or -1")
    half: int = Field(..., ge=1, le=2, description="1 = first half, 2 = second half")
    second_in_match: int = Field(
        ...,
        ge=0,
        description="Exact match time in seconds (0 = kick-off; 2700 = 45:00; 4042 = 67:22). Used for analytics.",
    )

    def validate_event(self):
        if self.event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"Unsupported event_type: {self.event_type}")
        if self.delta not in (-1, 1):
            raise ValueError("delta must be -1 or +1")
        return self


class MatchEventOut(BaseModel):
    """Event with exact match timestamp (half + second_in_match) for analytics."""

    id: int
    match_id: int
    player_id: int
    event_type: str
    delta: int
    half: int
    second_in_match: int  # total seconds into match (0 = kick-off)

    class Config:
        from_attributes = True