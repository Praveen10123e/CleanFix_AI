from typing import Optional
from pydantic import BaseModel, Field

from backend.app.schemas.user import UserRead


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=10, description="Google OAuth 2.0 ID Token")


class AuthTokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: Optional[int] = None
