import uuid
from enum import StrEnum
from typing import Annotated

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.db.models import Base, Group

Timestamp = Annotated[
    DateTime, mapped_column(DateTime, server_default=func.now())
]


class Role(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    surname: Mapped[str] = mapped_column(String(50), nullable=False)
    username: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(15), nullable=True)
    email: Mapped[str] = mapped_column(
        String(), nullable=False, unique=True, index=True
    )
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER)
    image_s3_path: Mapped[str] = mapped_column(String(), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[Timestamp]
    modified_at: Mapped[Timestamp] = mapped_column(
        server_default=func.now(), onupdate=func.current_timestamp()
    )

    # Foreign Key to Group
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"), nullable=True, index=True
    )

    # Relationship
    group: Mapped[Group] = relationship("Group", back_populates="users")

    def __repr__(self) -> str:
        return f"<User id: {self.id}, username: {self.username}>"
