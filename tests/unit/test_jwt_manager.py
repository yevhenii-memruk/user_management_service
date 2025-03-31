from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException

from src.settings import settings
from src.utils.jwt_manager import JWTManager, get_jwt_manager


@pytest.fixture
def jwt_manager() -> JWTManager:
    """Fixture to provide an instance of PasswordManager."""
    return get_jwt_manager()


def test_access_token_creation(jwt_manager: JWTManager) -> None:
    """Test creating and validating access tokens."""
    user_payload = {
        "sub": "123e4567-e89b-12d3-a456-426614174000",
        "username": "testuser",
    }

    tokens = jwt_manager.get_tokens(user_payload)

    # Check token types
    assert isinstance(tokens.access_token, str)
    assert isinstance(tokens.refresh_token, str)

    # Decode the access token
    decoded_payload = jwt_manager.decode_jwt_token(tokens.access_token)

    assert decoded_payload["sub"] == user_payload["sub"]
    assert decoded_payload["username"] == user_payload["username"]
    assert "exp" in decoded_payload

    # Check expiration is in the future
    exp_time = datetime.fromtimestamp(decoded_payload["exp"], tz=timezone.utc)
    assert exp_time > datetime.now(timezone.utc)


def test_refresh_token_creation(jwt_manager: JWTManager) -> None:
    """Test that refresh tokens are properly generated."""
    tokens = jwt_manager.get_tokens({"sub": "test_user_id"})

    assert isinstance(tokens.refresh_token, str)
    assert len(tokens.refresh_token) == jwt_manager.refresh_token_len * 2


def test_token_expiry(jwt_manager: JWTManager) -> None:
    """Test that an expired token raises an exception."""
    expired_token = jwt.encode(
        {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        jwt_manager.secret_key,
        algorithm=jwt_manager.algorithm,
    )

    with pytest.raises(HTTPException) as exc_info:
        jwt_manager.decode_jwt_token(expired_token)

    assert exc_info.value.status_code == 401
    assert "Token has expired" in exc_info.value.detail


def test_invalid_token(jwt_manager: JWTManager) -> None:
    """Test that an invalid token raises an exception."""
    invalid_token = "invalid.jwt.token"

    with pytest.raises(HTTPException) as exc_info:
        jwt_manager.decode_jwt_token(invalid_token)

    assert exc_info.value.status_code == 401
    assert "Failed to decode token" in exc_info.value.detail


def test_wrong_secret_key() -> None:
    """Test decoding with a wrong secret key fails."""
    # Create a token with the correct secret
    correct_jwt_manager = JWTManager(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        expires_minutes=settings.JWT_ACCESS_TOKEN_EXPIRATION_SECONDS,
    )

    user_payload = {"sub": "user123"}
    tokens = correct_jwt_manager.get_tokens(user_payload)

    # Try decoding with the WRONG secret key
    wrong_jwt_manager = JWTManager(
        secret_key="wrong_secret_key",
        algorithm=settings.JWT_ALGORITHM,
        expires_minutes=settings.JWT_ACCESS_TOKEN_EXPIRATION_SECONDS,
    )

    with pytest.raises(HTTPException) as exc_info:
        wrong_jwt_manager.decode_jwt_token(tokens.access_token)

    assert exc_info.value.status_code == 401
    assert "Invalid signature" in exc_info.value.detail


def test_invalid_algorithm(jwt_manager: JWTManager) -> None:
    """Test that a token signed with a different algorithm fails."""
    different_alg_token = jwt.encode(
        {"sub": "user123"},
        jwt_manager.secret_key,
        algorithm="HS512",
    )

    with pytest.raises(HTTPException) as exc_info:
        jwt_manager.decode_jwt_token(different_alg_token)

    assert exc_info.value.status_code == 401
    assert "Invalid token" in exc_info.value.detail
