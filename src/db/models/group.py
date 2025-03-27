from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models import Base
from src.db.models.user import Timestamp

if TYPE_CHECKING:
    from src.db.models.user import User


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[Timestamp]

    # Relationship
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="group", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Group id: {self.id}, name: {self.name}>"
