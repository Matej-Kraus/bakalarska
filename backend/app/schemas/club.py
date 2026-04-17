from pydantic import BaseModel, Field


class ClubOut(BaseModel):
    id: int
    name: str
    short_name: str | None = None
    city: str | None = None
    home_venue: str | None = None
    founded_year: int | None = None

    class Config:
        from_attributes = True


class ClubUpdate(BaseModel):
    """Coach can update club profile. Name must stay non-empty."""

    name: str = Field(..., min_length=1, max_length=200)
    short_name: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=100)
    home_venue: str | None = Field(default=None, max_length=200)
    founded_year: int | None = Field(default=None, ge=1800, le=2100)
