import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import Form
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.db.models.user import Role


class UserSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    surname: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone_number: str
    group_id: Optional[int] = None
    role: Optional[Role] = None
    image_s3_path: Optional[str] = None

    @field_validator("phone_number")
    def validate_polish_phone(cls, value: str) -> str:
        if not re.fullmatch(r"\+48\d{9}$", value):
            raise ValueError(
                "Polish phone number must be in format '+48XXXXXXXXX'"
            )
        return value


class UserCreateSchema(UserSchema):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    role: Optional[Role] = None
    is_blocked: Optional[bool] = None

    @classmethod
    def as_form(
        cls,
        name: Optional[str] = Form(None, min_length=1),
        surname: Optional[str] = Form(None, min_length=1),
        username: Optional[str] = Form(None, min_length=3),
        email: Optional[EmailStr] = Form(None),
        phone_number: Optional[str] = Form(None),
        role: Optional[str] = Form(None),  # Or Enum if required
        is_blocked: Optional[bool] = Form(None),
    ) -> "UserUpdateSchema":
        return cls(
            name=name,
            surname=surname,
            username=username,
            email=email,
            phone_number=phone_number,
            role=role,
            is_blocked=is_blocked,
        )


class UserInDB(UserSchema):
    id: UUID
    created_at: datetime
    modified_at: datetime
    is_blocked: Optional[bool] = None

    # Allows Pydantic to extract data from SQLAlchemy ORM models,
    # treating them like dictionaries
    model_config = ConfigDict(from_attributes=True)


class UserResponseSchema(UserInDB):
    pass


class UserImageS3PathSchema(BaseModel):
    id: UUID
    username: str
    image_s3_path: Optional[str] = None
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
