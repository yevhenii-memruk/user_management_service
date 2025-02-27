from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import UUID4, BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"
    USER = "USER"


class UserSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    surname: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)


class UserCreateSchema(UserSchema):
    password: str = Field(..., min_length=8, max_length=128)
    group_id: Optional[int] = None


class UserResponseSchema(UserSchema):
    id: UUID4
    role: UserRole
    is_blocked: bool = False
    created_at: datetime
    modified_at: datetime
    group_id: Optional[int] = None

    # Allows Pydantic to extract data from SQLAlchemy ORM models,
    # treating them like dictionaries
    model_config = ConfigDict(from_attributes=True)


class UserUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    role: Optional[UserRole] = None
    is_blocked: Optional[bool] = None
