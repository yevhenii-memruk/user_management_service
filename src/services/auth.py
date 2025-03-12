import logging
import uuid
from typing import Optional, cast

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.schemas.auth import TokenResponse
from src.settings import settings
from src.utils.jwt_manager import JWTManager
from src.utils.password_manager import PasswordManager

logger = logging.getLogger(f"ums.{__name__}")


def get_jwt_manager() -> JWTManager:
    return JWTManager(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        expires_minutes=settings.JWT_EXPIRE_MINUTES,
    )


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

        # Create access and refresh tokens
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
                settings.JWT_EXPIRE_DAYS * 86400,  # Convert days to seconds
                str(user.id),
            )
            print(f"Redis key set: refresh_token:{refresh_token}")
        except Exception as e:
            print(f"Redis Error: {str(e)}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.get(User, uuid.UUID(user_id))
        return result

    async def refresh_tokens(
        self, refresh_token: str, user: User
    ) -> tuple[str, str]:
        """
        Validate a refresh token, blacklist it, and issue new tokens.

        Args:
            refresh_token: The refresh token to validate
            user: The user to validate

        Returns:
            Tuple of (new_access_token, new_refresh_token)
        """
        # Create payload for access token
        payload = {
            "sub": user.username,
            "role": user.role,
            "group_id": user.group_id,
        }

        tokens = self.jwt_manager.get_tokens(payload)
        access_token = tokens.access_token
        refresh_token = tokens.refresh_token

        # Store refresh token in Redis with user ID
        await self.redis_client.setex(
            f"refresh_token:{refresh_token}",
            settings.JWT_EXPIRE_DAYS * 86400,
            str(user.id),
        )

        return access_token, refresh_token
