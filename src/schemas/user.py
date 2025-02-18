from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import UUID4, BaseModel, EmailStr, Field


class Role(str, Enum):
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"
    USER = "USER"


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    surname: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserDisplay(UserBase):
    id: UUID4
    role: Role
    is_blocked: bool = False
    created_at: datetime
    modified_at: datetime
    group_id: Optional[int] = None

    # Allows Pydantic to extract data from SQLAlchemy ORM models,
    # treating them like dictionaries
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr]
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    role: Optional[Role]
    is_blocked: Optional[bool]
