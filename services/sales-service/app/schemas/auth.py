"""Auth/user contracts (SPEC-AUTH-001, skill pydantic: Create/Update/Read)."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    rol: Literal["admin", "cajero"]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    rol: str
    activo: bool


class UserUpdate(BaseModel):
    rol: Literal["admin", "cajero"] | None = None
    activo: bool | None = None
    password: str | None = Field(default=None, min_length=8)
