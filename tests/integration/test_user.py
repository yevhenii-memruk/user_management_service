import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_user_me(
    client: AsyncClient, user_token_headers, test_user
) -> None:
    """Test getting current user info."""
    response = await client.get("/user/me", headers=user_token_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["name"] == test_user.name
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_update_user_me(client: AsyncClient, user_token_headers) -> None:
    """Test updating current user info."""
    update_data = {
        "name": "updated_name",
        "surname": "updated_surname",
        "username": "string",
        "email": "user@example.com",
        "phone_number": "+48123321123",
        "role": "USER",
        "is_blocked": True,
    }

    response = await client.patch(
        "/user/me", data=update_data, headers=user_token_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["surname"] == update_data["surname"]


@pytest.mark.asyncio
async def test_delete_user_me(client: AsyncClient, user_token_headers) -> None:
    """Test deleting current user."""
    response = await client.delete("/user/me", headers=user_token_headers)

    assert response.status_code == 204

    # Try to get user info after deletion - should fail
    get_response = await client.get("/user/me", headers=user_token_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_by_id_admin(
    client: AsyncClient, admin_token_headers, test_user
) -> None:
    """Test admin getting user info by ID."""
    response = await client.get(
        f"/user/{test_user.id}", headers=admin_token_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["name"] == test_user.name


@pytest.mark.asyncio
async def test_get_user_by_id_moderator_same_group(
    client: AsyncClient, moderator_token_headers, test_user
) -> None:
    """Test moderator getting user info by ID (same group)."""
    response = await client.get(
        f"/user/{test_user.id}", headers=moderator_token_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_get_user_by_id_regular_user_forbidden(
    client: AsyncClient, user_token_headers, test_admin
) -> None:
    """Test regular user attempting to get another user's info."""
    response = await client.get(
        f"/user/{test_admin.id}", headers=user_token_headers
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_update_user_by_id_admin(
    client: AsyncClient, admin_token_headers, test_user
) -> None:
    """Test admin updating user info by ID."""
    update_data = {
        "name": "Admin Updated",
        "surname": "string",
        "username": "admin_updated",
        "email": "admin_updated@example.com",
        "phone_number": "+48000000000",
        "role": "USER",
        "is_blocked": True,
    }

    response = await client.patch(
        f"/user/{test_user.id}", json=update_data, headers=admin_token_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["is_blocked"] == update_data["is_blocked"]


@pytest.mark.asyncio
async def test_update_user_by_id_non_admin_forbidden(
    client: AsyncClient, moderator_token_headers, test_user
) -> None:
    """Test non-admin attempting to update user."""
    update_data = {"name": "Should Fail"}

    response = await client.patch(
        f"/user/{test_user.id}",
        json=update_data,
        headers=moderator_token_headers,
    )

    assert response.status_code == 403  # Forbidden
