from pydantic import BaseModel, Field, model_validator

from app.common.enums import EventType

# Re-export for backward compatibility
ALLOWED_EVENT_TYPES = {e.value for e in EventType}


class MatchEventCreate(BaseModel):
    """Event recorded during a live match. second_in_match = total seconds into the match (0 = kick-off 1st half)."""

    player_id: int
    event_type: EventType
    delta: int = Field(..., description="Use +1 or -1")
    half: int = Field(..., ge=1, le=2, description="1 = first half, 2 = second half")
    second_in_match: int = Field(
        ...,
        ge=0,
        description="Exact match time in seconds (0 = kick-off; 2700 = 45:00). Used for analytics.",
    )

    @model_validator(mode="after")
    def validate_delta(self):
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
    second_in_match: int

    class Config:
        from_attributes = True
