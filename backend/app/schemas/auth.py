from typing import Literal

from pydantic import BaseModel

UserRoleLiteral = Literal["coach", "assistant"]


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    club_name: str
    email: str
    password: str
    role: UserRoleLiteral = "coach"


class RegisterOut(BaseModel):
    ok: bool = True
    message: str


class UserOut(BaseModel):
    id: int
    club_id: int
    email: str
    role: UserRoleLiteral
    email_verified: bool

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
