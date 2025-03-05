from typing import Optional
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.schemas.user import UserCreateSchema, UserUpdateSchema
from src.utils.password_manager import PasswordManager


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.password_manager = PasswordManager()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_user_by_email(self, email: EmailStr) -> Optional[User]:
        """Get a user by email"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalars().first()

    async def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """Get a user by phone number"""
        result = await self.db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalars().first()

    async def get_user_by_email_or_username(
        self, email: EmailStr, username: str
    ) -> Optional[User]:
        """Get a user by email or username"""
        result = await self.db.execute(
            select(User).where(
                or_(User.email == email, User.username == username)
            )
        )
        return result.scalars().first()

    async def create_user(self, user_data: UserCreateSchema) -> User:
        """Create a new user"""
        user = User(
            name=user_data.name,
            surname=user_data.surname,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            phone_number=user_data.phone_number,
            group_id=user_data.group_id,
        )

        # Add to database
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update_user(
        self, user_id: UUID, user_data: UserUpdateSchema
    ) -> Optional[User]:
        """Update a user by ID"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Update user fields
        update_data = user_data.model_dump(exclude_unset=True)

        # Hash password if it's provided
        if "password" in update_data and update_data["password"]:
            update_data["password"] = self.password_manager.get_hash(
                update_data["password"]
            )

        # Update user fields
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def delete_user(self, user_id: UUID) -> bool:
        """Delete a user by ID"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()

        return True
