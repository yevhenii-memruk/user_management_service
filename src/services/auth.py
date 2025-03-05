import uuid
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.schemas.auth import TokenResponse
from src.utils.jwt_manager import JWTManager
from src.utils.password_manager import PasswordManager


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.password_manager = PasswordManager()

    async def authenticate_user(
        self,
        login: str,
        password: str,
        jwt_manager: JWTManager = Depends(JWTManager),
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
            password, user.password
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
        tokens = jwt_manager.get_tokens(
            payload={
                "sub": user.username,
                "role": user.role,
                "group_id": user.group_id,
            }
        )
        access_token = tokens.access_token
        refresh_token = tokens.refresh_token

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
        # return {
        #     "access_token": access_token,
        #     "refresh_token": refresh_token,
        #     "token_type": "bearer",
        # }

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.get(User, uuid.UUID(user_id))
        return result
