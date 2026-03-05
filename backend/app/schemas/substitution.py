from pydantic import BaseModel, Field


class SubstitutionCreate(BaseModel):
    player_out_id: int
    player_in_id: int
    half: int = Field(..., ge=1, le=2)
    second_in_match: int = Field(..., ge=0)


class SubstitutionOut(BaseModel):
    id: int
    match_id: int
    player_out_id: int
    player_in_id: int
    half: int
    second_in_match: int

    class Config:
        from_attributes = True

