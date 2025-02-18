from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenRefreshRequest(Token):
    refresh_token: str = Field(..., min_length=20)


class TokenData(BaseModel):
    username: str = Field(..., min_length=1)
