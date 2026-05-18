import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserIn:
    class Create(BaseModel):
        username: str
        password: str

    class Login(BaseModel):
        username: str
        password: str


class UserTokenPayload(BaseModel):
    jti: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int


class UserOut:

    class Base(BaseModel):
        created_at: datetime
        updated_at: datetime
        deleted_at: datetime | None
        id: int

    class Create(Base):
        username: str

    class Me(Base):
        username: str
        password: str
        refresh_token: str


class TokenResponse(BaseModel):
    user_id: int
    username: str
    access_token: str | None
    refresh_token: str | None
    token_type: str
