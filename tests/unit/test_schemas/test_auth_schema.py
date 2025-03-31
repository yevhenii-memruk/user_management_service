import pytest
from pydantic import ValidationError

from src.schemas.auth import (
    LoginRequest,
    PasswordResetRequest,
    TokenData,
    TokenRefreshRequest,
    TokenResponse,
)


class TestTokenResponse:
    def test_valid_token_response(self) -> None:
        token_data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        }
        token = TokenResponse(**token_data)
        assert token.access_token == token_data["access_token"]
        assert token.refresh_token == token_data["refresh_token"]
        assert token.token_type == "bearer"  # Default value


class TestTokenRefreshRequest:
    def test_valid_refresh_token(self) -> None:
        data = {
            "refresh_token": "valid_refresh_token_string_that_is_long_enough"
        }
        refresh_request = TokenRefreshRequest(**data)
        assert refresh_request.refresh_token == data["refresh_token"]

    def test_invalid_refresh_token(self) -> None:
        # Test token that is too short
        with pytest.raises(ValidationError) as exc_info:
            TokenRefreshRequest(refresh_token="tooshort")
        assert "String should have at least 20 characters" in str(
            exc_info.value
        )


class TestTokenData:
    def test_valid_token_data(self) -> None:
        data = {"username": "johndoe"}
        token_data = TokenData(**data)
        assert token_data.username == data["username"]

    def test_invalid_token_data(self) -> None:
        # Test empty username
        with pytest.raises(ValidationError) as exc_info:
            TokenData(username="")
        assert "String should have at least 1 character" in str(exc_info.value)


class TestLoginRequest:
    def test_valid_login_request(self) -> None:
        data = {"login": "johndoe", "password": "password123"}
        login_request = LoginRequest(**data)
        assert login_request.login == data["login"]
        assert login_request.password == data["password"]

    @pytest.mark.parametrize(
        "field,value,expected_error",
        [
            ("login", "", "String should have at least 1 character"),
            ("password", "", "String should have at least 1 character"),
        ],
    )
    def test_invalid_login_request(
        self, field: str, value: str, expected_error: str
    ) -> None:
        data = {"login": "johndoe", "password": "password123"}
        data[field] = value
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(**data)
        assert expected_error in str(exc_info.value)


class TestPasswordResetRequest:
    def test_valid_password_reset(self) -> None:
        data = {"email": "john.doe@example.com"}
        reset_request = PasswordResetRequest(**data)
        assert reset_request.email == data["email"]

    def test_invalid_email(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            PasswordResetRequest(email="invalid_email")
        assert "value is not a valid email address" in str(exc_info.value)
