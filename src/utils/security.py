from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Union

import jwt
from passlib.context import CryptContext

from src.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify if a password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(
    data: Dict[str, Any], expires_delta: Union[timedelta, None] = None
) -> str:
    """Generate a JWT token with an expired time."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_access_token(user_id: str, role: str) -> str:
    """Generate an access token (short-lived)."""
    return create_jwt_token(
        {"user_id": user_id, "role": role},
        timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    """Generate a refresh token (longer-lived)."""
    return create_jwt_token(
        {"user_id": user_id}, timedelta(days=settings.JWT_EXPIRE_DAYS)
    )


def decode_jwt_token(token: str) -> Union[Dict[str, Any], Exception]:
    """Verify and decode a JWT token."""
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        return e
