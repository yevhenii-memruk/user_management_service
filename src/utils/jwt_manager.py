import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, status


@dataclass(frozen=True, slots=True)
class Tokens:
    access_token: str
    refresh_token: str


class JWTManager:
    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        expires_minutes: int,
        refresh_token_len: int = 64,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expires_minutes = expires_minutes
        self.refresh_token_len = refresh_token_len

    def _create_jwt_token(
        self, data: dict[str, Any], token_type: str = "access"
    ) -> str:
        """Generate a JWT token with an expired time."""
        payload = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.expires_minutes
        )
        payload.update({"exp": expire, "type": token_type})

        return jwt.encode(
            payload=payload,
            key=self.secret_key,
            algorithm=self.algorithm,
        )

    def get_tokens(self, payload: dict) -> Tokens:
        """Generate both access and refresh tokens."""
        payload_copy = payload.copy()
        access_token = self._create_jwt_token(payload_copy, "access")
        refresh_token = secrets.token_hex(self.refresh_token_len)

        return Tokens(access_token, refresh_token)

    def decode_jwt_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                jwt=token,
                key=self.secret_key,
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

        return payload
