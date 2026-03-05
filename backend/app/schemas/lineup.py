from pydantic import BaseModel, Field

class LineupItem(BaseModel):
    player_id: int
    jersey_number_match: int = Field(..., ge=0)
    role: str  # "starter" | "sub"

class LineupSaveRequest(BaseModel):
    items: list[LineupItem]

class LineupItemOut(LineupItem):
    pass

class LineupEditorPlayer(BaseModel):
    player_id: int
    first_name: str
    last_name: str
    default_jersey_number: int
    role: str  # "starter" | "sub" | "out"
    jersey_number_match: int | None = None

class LineupEditorResponse(BaseModel):
    match_id: int
    taken_numbers: list[int]
    players: list[LineupEditorPlayer]