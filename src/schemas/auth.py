from pydantic import BaseModel, EmailStr, Field

from src.schemas.user import UserCreateSchema


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20)


class TokenData(BaseModel):
    username: str = Field(..., min_length=1)


class SignupRequest(UserCreateSchema):
    pass


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


# Schema for password reset
class PasswordResetRequest(BaseModel):
    email: EmailStr
