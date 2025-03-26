import pytest
from httpx import AsyncClient

from src.db.models import User


@pytest.mark.asyncio
async def test_signup(client: AsyncClient) -> None:
    signup_data = {
        "name": "John",
        "surname": "Doe",
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "phone_number": "+48123456789",
        "group_id": None,  # Optional
        "role": "USER",  # Enum
        "image_s3_path": None,  # Optional
    }

    response = await client.post("/auth/signup", json=signup_data)
    data = response.json()

    assert response.status_code == 201
    assert "id" in data
    assert data["email"] == signup_data["email"]
    assert data["name"] == signup_data["name"]
    assert "password" not in data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "duplicate_field", ["email", "username", "phone_number"]
)
async def test_signup_duplicate(
    client: AsyncClient, test_user: User, duplicate_field: str
) -> None:
    """
    Test signup failure when trying to register with an existing email, username, or phone number.
    """
    signup_data = {
        "name": "Duplicate",
        "surname": "User",
        "username": "dupuser",
        "email": "duplicate@example.com",
        "phone_number": "+48887766555",
        "password": "Password123!",
        "role": "USER",
        "group_id": None,
    }

    signup_data[duplicate_field] = getattr(test_user, duplicate_field)

    response = await client.post("/auth/signup", json=signup_data)

    assert response.status_code == 409
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
@pytest.mark.parametrize("login_field", ["email", "username", "phone_number"])
async def test_login(
    client: AsyncClient, test_user: User, login_field: str
) -> None:
    """Test successful login with email, username and phone_number."""
    login_data = {
        "login": getattr(test_user, login_field),
        "password": "userpassword",
    }

    response = await client.post("/auth/login", json=login_data)
    data = response.json()

    assert response.status_code == 200
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient) -> None:
    """Test login with invalid credentials."""
    login_data = {
        "login": "nonexistent@example.com",
        "password": "wrongpassword",
    }

    response = await client.post("/auth/login", json=login_data)

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
