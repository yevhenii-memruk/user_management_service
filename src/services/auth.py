import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, cast

from fastapi import HTTPException, status
from pydantic import EmailStr
from redis.asyncio import Redis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.schemas.auth import TokenResponse
from src.settings import settings
from src.utils.exceptions import InvalidTokenError, UserNotFoundError
from src.utils.jwt_manager import JWTManager
from src.utils.password_manager import PasswordManager

logger = logging.getLogger(f"ums.{__name__}")


def get_jwt_manager() -> JWTManager:
    return JWTManager(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        expires_minutes=settings.JWT_EXPIRE_MINUTES,
    )


def create_rabbitmq_message(user: User) -> dict[str, Any]:
    reset_token = str(uuid.uuid4())

    # Create reset link
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    # Prepare message for RabbitMQ
    message = {
        "email": user.email,
        "subject": "Password Reset Request",
        "body": f"Click the following link to reset your password: {reset_link}",
        "datetime": datetime.now(timezone.utc).isoformat(),
        "user_id": str(user.id),
        "reset_token": reset_token,
    }

    return message


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
        # Try to find user by email or username
        result = await self.db.execute(
            select(User).where(
                or_(User.email == login, User.username == login)
            )
        )
        user = result.scalars().first()

        if not user or not self.password_manager.verify_password(
            plain_password=password, hashed_password=cast(str, user.password)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect login or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is blocked",
                headers={"WWW-Authenticate": "Bearer"},
            )
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
                settings.JWT_EXPIRE_DAYS * 86400,
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
        is_blacklisted = await self.redis_client.exists(
            f"blacklist:{refresh_token}"
        )
        if is_blacklisted:
            raise InvalidTokenError("Invalid or expired token")

        # Get the user ID associated with this refresh token
        user_id = await self.redis_client.get(f"refresh_token:{refresh_token}")
        if not user_id:
            raise InvalidTokenError("Invalid token")

        # Delete old refresh token and blacklist it in one atomic operation
        await self.redis_client.delete(f"refresh_token:{refresh_token}")
        await self.redis_client.setex(
            f"blacklist:{refresh_token}", 3600, "blacklisted"
        )

        # Get the user
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError()

        # Create and return new tokens
        return await self._create_user_tokens(user)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.get(User, uuid.UUID(user_id))
        return result

    async def get_user_by_email(self, email: EmailStr) -> Optional[User]:
        result = await self.db.get(User, email)
        return result
