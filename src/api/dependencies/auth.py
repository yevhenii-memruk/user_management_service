from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.database import get_session
from src.db.models.user import Role, User
from src.services.user import UserService
from src.utils.exceptions import (
    InvalidTokenDataError,
    NotEnoughPermissionsError,
    UserBlockedError,
    UserNotFoundError,
)
from src.utils.jwt_bearer import JWTBearer


async def get_current_user(
    payload: dict = Depends(JWTBearer()),
    db: AsyncSession = Depends(get_session),
) -> User:
    """
    Dependency to get the current user from the JWT token payload.
    """
    username = payload.get("sub")
    if not username:
        raise InvalidTokenDataError()

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)

    if not user:
        raise UserNotFoundError()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get the current active user.
    """
    if current_user.is_blocked:
        raise UserBlockedError()

    return current_user


async def check_admin_access(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to check if the current user has admin role.
    """
    if current_user.role != Role.ADMIN:
        raise NotEnoughPermissionsError()

    return current_user


async def check_moderator_access(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to check if the current user has moderator or admin role.
    """
    if current_user.role not in [Role.ADMIN, Role.MODERATOR]:
        raise NotEnoughPermissionsError()

    return current_user
