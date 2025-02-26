import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import FastAPI, HTTPException, status

from src.settings import settings


@dataclass
class Tokens:
    access_token: str
    refresh_token: str


class JWTManager:
    def __init__(self, app: FastAPI):
        self.key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expires_days = settings.JWT_EXPIRATION_DAYS
        self.expires_minutes = settings.JWT_EXPIRATION_MINUTES
        self.refresh_token_len = 64

    def _create_jwt_token(
        self, data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """Generate a JWT token with an expired time."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)

        to_encode.update({"exp": expire})

        return jwt.encode(
            payload=to_encode,
            key=self.key,
            algorithm=self.algorithm,
        )

    def get_tokens(self, payload: dict) -> Tokens:
        """Generate both access and refresh tokens."""

        # Generate an access token (short-lived).
        access_token = self._create_jwt_token(
            payload,
            timedelta(minutes=self.expires_minutes),
        )

        refresh_token = secrets.token_hex(self.refresh_token_len)

        return Tokens(access_token, refresh_token)

    def get_payload(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            return jwt.decode(
                jwt=token,
                key=self.key,
                algorithms=[self.algorithm],
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
