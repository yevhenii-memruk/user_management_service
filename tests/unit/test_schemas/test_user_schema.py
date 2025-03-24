from datetime import datetime
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.db.models.user import Role
from src.schemas.user import (
    UserCreateSchema,
    UserImageS3PathSchema,
    UserResponseSchema,
    UserSchema,
    UserUpdateSchema,
)


@pytest.fixture
def valid_user_base_data() -> dict[str, str]:
    return {
        "name": "John",
        "surname": "Doe",
        "username": "johndoe",
        "email": "john.doe@example.com",
        "phone_number": "+48123456789",
    }


@pytest.fixture
def valid_user_create_data(
    valid_user_base_data: dict[str, str],
) -> dict[str, str]:
    return {**valid_user_base_data, "password": "PASSWORD"}


@pytest.fixture
def valid_user_display_data(
    valid_user_base_data: dict[str, str],
) -> dict[str, Any]:
    return {
        **valid_user_base_data,
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "role": "USER",
        "is_blocked": False,
        "created_at": datetime.now(),
        "modified_at": datetime.now(),
        "group_id": 1,
    }


class TestUserBase:
    def test_valid_user_base(
        self, valid_user_base_data: dict[str, str]
    ) -> None:
        user = UserSchema(**valid_user_base_data)
        assert user.name == valid_user_base_data["name"]
        assert user.surname == valid_user_base_data["surname"]
        assert user.username == valid_user_base_data["username"]
        assert user.email == valid_user_base_data["email"]
        assert user.phone_number == valid_user_base_data["phone_number"]

    @pytest.mark.parametrize(
        "field,value,expected_error",
        [
            ("name", "", "String should have at least 1 character"),
            ("name", "a" * 101, "String should have at most 100 characters"),
            ("surname", "", "String should have at least 1 character"),
            (
                "surname",
                "a" * 101,
                "String should have at most 100 characters",
            ),
            ("username", "ab", "String should have at least 3 characters"),
            (
                "username",
                "a" * 101,
                "String should have at most 100 characters",
            ),
            ("email", "invalid_email", "value is not a valid email address"),
            (
                "phone_number",
                "123",
                "Polish phone number must be in format '+48XXXXXXXXX'",
            ),
            (
                "phone_number",
                "1" * 16,
                "Polish phone number must be in format '+48XXXXXXXXX'",
            ),
        ],
    )
    def test_invalid_user_base(
        self,
        valid_user_base_data: dict[str, str],
        field: str,
        value: str,
        expected_error: str,
    ) -> None:
        data = valid_user_base_data.copy()
        data[field] = value
        with pytest.raises(ValidationError) as exc_info:
            UserSchema(**data)
        assert expected_error in str(exc_info.value)


class TestUserCreate:
    def test_valid_user_create(
        self, valid_user_create_data: dict[str, str]
    ) -> None:
        user = UserCreateSchema(**valid_user_create_data)
        assert user.password == valid_user_create_data["password"]

    @pytest.mark.parametrize(
        "password,expected_error",
        [
            ("short", "String should have at least 8 characters"),
            ("a" * 129, "String should have at most 128 characters"),
        ],
    )
    def test_invalid_password(
        self,
        valid_user_create_data: dict[str, str],
        password: str,
        expected_error: str,
    ) -> None:
        data = valid_user_create_data.copy()
        data["password"] = password
        with pytest.raises(ValidationError) as exc_info:
            UserCreateSchema(**data)
        assert expected_error in str(exc_info.value)


class TestUserDisplay:
    def test_valid_user_display(
        self, valid_user_display_data: dict[str, str]
    ) -> None:
        user = UserResponseSchema(**valid_user_display_data)
        assert isinstance(user.id, UUID)
        assert user.role == Role.USER
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.modified_at, datetime)
        assert user.group_id == 1

    @pytest.mark.parametrize("role", ["ADMIN", "MODERATOR", "USER"])
    def test_valid_roles(
        self, valid_user_display_data: dict[str, str], role: Role
    ) -> None:
        data = valid_user_display_data.copy()
        data["role"] = role
        user = UserResponseSchema(**data)
        assert user.role == Role(role)

    def test_invalid_role(
        self, valid_user_display_data: dict[str, str]
    ) -> None:
        data = valid_user_display_data.copy()
        data["role"] = "INVALID_ROLE"
        with pytest.raises(ValidationError) as exc_info:
            UserResponseSchema(**data)
        assert " Input should be 'USER', 'ADMIN' or 'MODERATOR'" in str(
            exc_info.value
        )


class TestUserUpdate:
    def test_empty_update(self) -> None:
        user = UserUpdateSchema()
        assert all(value is None for value in user.model_dump().values())

    def test_partial_update(
        self, valid_user_base_data: dict[str, str]
    ) -> None:
        update_data = {"name": "Jane", "email": "jane.doe@example.com"}
        user = UserUpdateSchema(**update_data)
        assert user.name == "Jane"
        assert user.email == "jane.doe@example.com"
        assert user.surname is None
        assert user.username is None
        assert user.phone_number is None
        assert user.role is None
        assert user.is_blocked is None

    @pytest.mark.parametrize(
        "field,value,expected_error",
        [
            ("name", "a" * 101, "String should have at most 100 characters"),
            ("username", "ab", "String should have at least 3 characters"),
            ("email", "invalid_email", "value is not a valid email address"),
            (
                "phone_number",
                "123",
                "String should have at least 10 characters",
            ),
            (
                "role",
                "INVALID_ROLE",
                "Input should be 'USER', 'ADMIN' or 'MODERATOR'",
            ),
        ],
    )
    def test_invalid_update(
        self, field: str, value: str, expected_error: str
    ) -> None:
        data = {field: value}
        with pytest.raises(ValidationError) as exc_info:
            UserUpdateSchema(**data)
        assert expected_error in str(exc_info.value)


class TestUserImageS3Path:
    @pytest.fixture
    def valid_user_image_data(self) -> dict[str, Any]:
        return {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "username": "johndoe",
            "image_s3_path": "user-images/550e8400-e29b-41d4-a716-446655440000/profile.jpg",
            "image_url": "https://example.com/users/550e8400-e29b-41d4-a716-446655440000/profile.jpg",
        }

    def test_valid_user_image_schema(
        self, valid_user_image_data: dict[str, Any]
    ) -> None:
        user_image = UserImageS3PathSchema(**valid_user_image_data)
        assert isinstance(user_image.id, UUID)
        assert user_image.username == valid_user_image_data["username"]
        assert (
            user_image.image_s3_path == valid_user_image_data["image_s3_path"]
        )
        assert user_image.image_url == valid_user_image_data["image_url"]

    def test_optional_fields(self) -> None:
        # Test with only required fields
        user_image = UserImageS3PathSchema(
            id="550e8400-e29b-41d4-a716-446655440000", username="johndoe"
        )
        assert isinstance(user_image.id, UUID)
        assert user_image.username == "johndoe"
        assert user_image.image_s3_path is None
        assert user_image.image_url is None
