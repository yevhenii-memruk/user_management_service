from typing import List, Optional
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Group, User
from src.db.models.user import Role
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
        user = User(**user_data.model_dump())

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

    async def check_group_exists(self, group_id: int) -> bool:
        # Check if the group exists in the 'groups' table
        group = await self.db.execute(
            select(Group).where(Group.id == group_id)
        )
        if group:
            return True
        return False

    async def get_all_users(
        self,
        current_user: User,
        page: int,
        limit: int,
        filter_by_name: Optional[str] = None,
        sort_by: Optional[str] = None,
        order_by: str = "asc",
    ) -> List[User]:

        query = select(User)

        if current_user.role == Role.MODERATOR:
            # MODERATOR can only see users in their group
            query = query.join(Group).where(
                User.group_id == current_user.group_id
            )

        # Apply name filter if provided
        if filter_by_name:
            query = query.filter(User.name.ilike(f"%{filter_by_name}%"))

        # Handle sorting
        if sort_by is not None and hasattr(User, sort_by):
            order_column = getattr(User, sort_by)
        else:
            order_column = User.created_at

        # Apply sort direction
        if order_by == "asc":
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())

        # Apply pagination
        query = query.offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(query)
        return result.unique().scalars().all()
