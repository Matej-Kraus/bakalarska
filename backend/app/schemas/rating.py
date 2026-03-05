from pydantic import BaseModel, Field


class RatingItem(BaseModel):
    player_id: int
    rating: int = Field(..., ge=1, le=10)
    note: str | None = None


class RatingsSaveRequest(BaseModel):
    items: list[RatingItem]


class RatingOut(RatingItem):
    id: int
    match_id: int
    user_id: int

    class Config:
        from_attributes = True

