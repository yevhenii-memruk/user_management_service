from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Union

import jwt
from fastapi import HTTPException, status

from src.settings import settings


class JWTManager:
    @staticmethod
    def _create_jwt_token(
        data: Dict[str, Any], expires_delta: Union[timedelta, None] = None
    ) -> str:
        """Generate a JWT token with an expired time."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)

        to_encode.update({"exp": expire})

        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    def get_tokens(self, user_id: str, role: str) -> Dict[str, str]:
        """Generate both access and refresh tokens."""

        # Generate an access token (short-lived).
        access_token = self._create_jwt_token(
            {"user_id": user_id, "role": role},
            timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        )

        # Generate a refresh token (longer-lived).
        refresh_token = self._create_jwt_token(
            {"user_id": user_id}, timedelta(days=settings.JWT_EXPIRE_DAYS)
        )

        return {"access_token": access_token, "refresh_token": refresh_token}

    @staticmethod
    def get_payload(token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.DecodeError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to decode token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
