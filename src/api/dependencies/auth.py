import logging

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.database import get_session
from src.db.models.user import User
from src.schemas.user import UserResponseSchema
from src.services.user import UserService
from src.settings import settings
from src.utils.exceptions import (
    InvalidTokenDataError,
    UserBlockedError,
    UserNotFoundError,
)
from src.utils.jwt_bearer import JWTBearer
from src.utils.jwt_manager import JWTManager

logger = logging.getLogger(f"ums.{__name__}")

jwt_manager = JWTManager(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
    expires_minutes=settings.JWT_ACCESS_TOKEN_EXPIRATION_SECONDS,
)

jwt_bearer = JWTBearer(jwt_manager=jwt_manager)


async def get_current_user(
    payload: dict = Depends(jwt_bearer),
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
) -> UserResponseSchema:
    """
    Dependency to get the current active user.
    """
    if current_user.is_blocked:
        raise UserBlockedError()

    return UserResponseSchema.model_validate(current_user)
