import logging
import uuid
from typing import Optional, cast

from fastapi import HTTPException, status
from pydantic import EmailStr
from redis.asyncio import Redis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.schemas.auth import TokenResponse
from src.settings import settings
from src.utils.exceptions import (
    InvalidCredentialsException,
    InvalidTokenError,
    UserBlockedError,
    UserNotFoundError,
)
from src.utils.jwt_manager import get_jwt_manager
from src.utils.password_manager import PasswordManager

logger = logging.getLogger(f"ums.{__name__}")


class AuthService:
    def __init__(self, db: AsyncSession, redis_client: Redis):
        self.db = db
        self.password_manager = PasswordManager()
        self.jwt_manager = get_jwt_manager()
        self.redis_client = redis_client

    async def authenticate_user(
        self, login: str, password: str
    ) -> TokenResponse:
        """
        Authenticate a user by login (email or username) and password.
        """
        # Try to find user by email, username or phone number
        result = await self.db.execute(
            select(User).where(
                or_(
                    User.email == login,
                    User.username == login,
                    User.phone_number == login,
                )
            )
        )
        user = result.scalars().first()

        if not user:
            raise UserNotFoundError()

        if not self.password_manager.verify_password(
            plain_password=password, hashed_password=cast(str, user.password)
        ):
            raise InvalidCredentialsException()

        if user.is_blocked:
            raise UserBlockedError()

        return await self._create_user_tokens(user)

    async def _create_user_tokens(self, user: User) -> TokenResponse:
        """Create access and refresh tokens for a user and store in Redis"""
        # Create tokens
        tokens = self.jwt_manager.get_tokens(
            payload={
                "sub": user.username,
                "role": user.role,
                "group_id": user.group_id,
            }
        )
        access_token = tokens.access_token
        refresh_token = tokens.refresh_token

        # Store refresh token in Redis with user ID
        try:
            await self.redis_client.setex(
                f"refresh_token:{refresh_token}",
                settings.JWT_REFRESH_TOKEN_EXPIRATION_SECONDS * 86400,
                str(user.id),
            )
            logger.debug(f"Redis key set: refresh_token:{refresh_token}")
        except Exception as e:
            logger.error(f"Redis Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error",
            )

        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token
        )

    async def process_token_refresh(self, refresh_token: str) -> TokenResponse:
        """
        Process a token refresh request.
        Returns:
            TokenResponse with new access and refresh tokens
        """
        # Check if token is blacklisted
        try:
            is_blacklisted = await self.redis_client.exists(
                f"blacklist:{refresh_token}"
            )
            if is_blacklisted:
                raise InvalidTokenError("Invalid or expired token")

            # Get the user ID associated with this refresh token
            user_id = await self.redis_client.get(
                f"refresh_token:{refresh_token}"
            )
            if not user_id:
                raise InvalidTokenError("Invalid token")

            # Delete old refresh token and blacklist it in one atomic operation
            await self.redis_client.delete(f"refresh_token:{refresh_token}")
            await self.redis_client.setex(
                f"blacklist:{refresh_token}",
                settings.JWT_REFRESH_TOKEN_EXPIRATION_SECONDS,
                "blacklisted",
            )

            # Get the user
            user = await self.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(str(user_id))

            # Create and return new tokens
            return await self._create_user_tokens(user)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error {e} occurred",
            )

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.get(User, uuid.UUID(user_id))
        return result

    async def get_user_by_email(self, email: EmailStr) -> Optional[User]:
        result = await self.db.get(User, email)
        return result
