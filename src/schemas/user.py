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
    group_id: Optional[int] = None


class UserCreateSchema(UserSchema):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    role: Optional[UserRole] = None
    is_blocked: Optional[bool] = None


class UserInDB(UserSchema):
    id: UUID4
    created_at: datetime
    modified_at: datetime

    # Allows Pydantic to extract data from SQLAlchemy ORM models,
    # treating them like dictionaries
    model_config = ConfigDict(from_attributes=True)


class UserResponseSchema(UserInDB):
    pass
