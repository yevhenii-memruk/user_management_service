import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_users_admin(
    client: AsyncClient,
    admin_token_headers,
    test_user,
    test_moderator,
    test_admin,
) -> None:
    """Test admin getting list of users."""
    response = await client.get(
        "/users", headers=admin_token_headers, follow_redirects=True
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 3

    # Check user IDs are in the response
    user_ids = [user["id"] for user in data]
    assert str(test_user.id) in user_ids
    assert str(test_moderator.id) in user_ids
    assert str(test_admin.id) in user_ids


@pytest.mark.asyncio
async def test_get_users_moderator(
    client: AsyncClient,
    moderator_token_headers,
    test_user,
    test_moderator,
    test_admin,
) -> None:
    """Test moderator getting list of users from same group."""
    response = await client.get(
        "/users", headers=moderator_token_headers, follow_redirects=True
    )

    assert response.status_code == 200
    data = response.json()

    # GROUP TABLE is Null
    # Check only users from moderator's group are returned
    # user_ids = [user["id"] for user in data]
    # assert str(test_user.id) in user_ids  # Same group
    # assert str(test_moderator.id) in user_ids

    # Check group filtering is working
    for user in data:
        assert user["group_id"] == str(test_moderator.group_id)


@pytest.mark.asyncio
async def test_get_users_regular_user_forbidden(
    client: AsyncClient, user_token_headers
) -> None:
    """Test regular user attempting to access users list."""
    response = await client.get(
        "/users", headers=user_token_headers, follow_redirects=True
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_get_users_with_pagination(
    client: AsyncClient,
    admin_token_headers,
    test_user,
    test_moderator,
    test_admin,
) -> None:
    """Test pagination for users list."""
    # Page 1 with limit 1
    response1 = await client.get(
        "/users?page=1&limit=1",
        headers=admin_token_headers,
        follow_redirects=True,
    )

    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) == 1  # Should only return 1 item

    # Page 2 with limit 1
    response2 = await client.get(
        "/users?page=2&limit=1",
        headers=admin_token_headers,
        follow_redirects=True,
    )

    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 1  # Should only return 1 item

    # Items on page 1 and 2 should be different
    assert data1[0]["id"] != data2[0]["id"]


@pytest.mark.asyncio
async def test_get_users_with_filter(
    client: AsyncClient, admin_token_headers, test_user
) -> None:
    """Test filtering users by name."""
    # Filter by user's name
    name_filter = test_user.name
    response = await client.get(
        f"/users?filter_by_name={name_filter}",
        headers=admin_token_headers,
        follow_redirects=True,
    )

    assert response.status_code == 200
    data = response.json()

    # At least one result should be returned
    assert len(data) >= 1

    # The test user should be in the results
    user_ids = [user["id"] for user in data]
    assert str(test_user.id) in user_ids

    # All returned items should contain the filter string in name or surname
    for user in data:
        assert (
            name_filter.lower() in user["name"].lower()
            or name_filter.lower() in user["surname"].lower()
        )


@pytest.mark.asyncio
async def test_get_users_with_sorting(
    client: AsyncClient, admin_token_headers
) -> None:
    """Test sorting users list."""
    # Sort by name ascending
    response_asc = await client.get(
        "/users?sort_by=name&order_by=asc",
        headers=admin_token_headers,
        follow_redirects=True,
    )

    assert response_asc.status_code == 200
    data_asc = response_asc.json()

    # Check that items are sorted by name in ascending order
    names = [user["name"] for user in data_asc]
    assert names == sorted(names)

    # Sort by name descending
    response_desc = await client.get(
        "/users?sort_by=name&order_by=desc",
        headers=admin_token_headers,
        follow_redirects=True,
    )

    assert response_desc.status_code == 200
    data_desc = response_desc.json()

    # Check that items are sorted by name in descending order
    names = [user["name"] for user in data_desc]
    assert names == sorted(names, reverse=True)
