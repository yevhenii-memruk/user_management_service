import logging
from typing import Any, List, Literal, Optional
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Group, User
from src.db.models.user import Role
from src.schemas.user import (
    UserCreateSchema,
    UserResponseSchema,
    UserUpdateSchema,
)
from src.utils.exceptions import (
    GroupNotExistError,
    NotEnoughPermissionsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.utils.password_manager import PasswordManager

logger = logging.getLogger(f"ums.{__name__}")


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.password_manager = PasswordManager()

    async def get_user(self, **filter: dict[str, Any]) -> Optional[User]:
        """
        Retrieve a user using a single key-value pair.

        Usage:
        - `await get_user(id=user_id)`
        - `await get_user(email=email)`
        - `await get_user(username=username)`
        - `await get_user(phone_number=phone_number)`
        """

        logger.debug(f"filters: {filter}")

        key, value = filter.popitem()
        query = select(User).where(getattr(User, key) == value)
        result = await self.db.execute(query)
        if not result:
            raise UserNotFoundError()
        user = result.scalars().first()

        return user

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID"""
        return await self.get_user(id=user_id)

    async def get_user_by_email(self, email: EmailStr) -> Optional[User]:
        """Get a user by email"""
        return await self.get_user(email=email)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        return await self.get_user(username=username)

    async def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """Get a user by phone number"""
        return await self.get_user(phone_number=phone_number)

    async def check_if_user_exists(
        self, email: EmailStr, username: str, phone_number: str
    ) -> None:
        user = await self.db.execute(
            select(User).where(
                or_(
                    User.email == email,
                    User.username == username,
                    User.phone_number == phone_number,
                )
            )
        )
        result = user.scalars().first()
        if result:
            raise UserAlreadyExistsError()

    async def create_user(
        self, user_data: UserCreateSchema
    ) -> UserResponseSchema:
        # Check if User already exists, raise Error if exists
        await self.check_if_user_exists(
            user_data.email, user_data.username, user_data.phone_number
        )

        # Validate User group_id, checks if id exists in Group table
        if user_data.group_id:
            await self.check_group_exists(user_data.group_id)

        # Create new user with hashed password
        hashed_password = self.password_manager.get_hash(user_data.password)

        user = User(
            **user_data.model_dump(exclude={"password"}),
            password=hashed_password,
        )

        # Add to database
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return UserResponseSchema.model_validate(user)

    async def update_user(
        self, user_id: UUID, user_data: UserUpdateSchema
    ) -> Optional[User]:
        """Update a user by ID"""
        user = await self.get_user_by_id(user_id)

        # Update user fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def delete_user(self, user_id: UUID) -> None:
        """Delete a user by ID"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        await self.db.delete(user)
        await self.db.commit()

    async def check_group_exists(self, group_id: int) -> None:
        """Check if the group exists in the 'groups' table"""
        group = await self.db.execute(
            select(Group).where(Group.id == group_id)
        )
        if not group:
            raise GroupNotExistError(group_id)

    async def get_all_users(
        self,
        current_user: User,
        page: int,
        limit: int,
        filter_by_name: Optional[str] = None,
        sort_by: Optional[Literal["id", "name", "email", "created_at"]] = None,
        order_by: Literal["asc", "desc"] = "asc",
    ) -> List[User]:

        query = select(User)

        if current_user.role == Role.MODERATOR:
            # MODERATOR can only see users in their group
            query = query.join(Group).where(
                User.group_id == current_user.group_id
            )

        # Apply name filter if provided
        if filter_by_name:
            query = query.filter(
                or_(
                    User.name.ilike(f"%{filter_by_name}%"),
                    User.surname.ilike(f"%{filter_by_name}%"),
                )
            )

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

    @staticmethod
    async def check_user_access_permissions(
        current_user: User, target_user: Optional[User]
    ) -> None:
        """
        Check if the current user has permission to access the target user's info.
        """
        if target_user is None:
            raise UserNotFoundError()
        # Users with USER role cannot access other user's info
        if current_user.role == Role.USER:
            raise NotEnoughPermissionsError()

        # MODERATOR can only access users in their group
        if (
            current_user.role == Role.MODERATOR
            and current_user.group_id != target_user.group_id
        ):
            raise NotEnoughPermissionsError()

    @staticmethod
    async def check_admin_access_permissions(current_user: User) -> None:
        """Check if the current user is admin"""
        if current_user.role != Role.ADMIN:
            raise NotEnoughPermissionsError()
