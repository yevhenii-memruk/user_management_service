from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models import Base, User
from src.db.models.user import Timestamp


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[Timestamp]

    # Relationship
    users: Mapped[list[User]] = relationship(
        "User", back_populates="group", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Group id: {self.id}, name: {self.name}>"
