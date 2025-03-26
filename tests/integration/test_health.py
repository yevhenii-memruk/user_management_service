import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthcheck(client: AsyncClient) -> None:
    response = await client.get("/healthcheck", follow_redirects=True)
    assert response.status_code == 200
    assert response.json()["message"] == "ok"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert (
        "Welcome to User Management Microservice" in response.json()["message"]
    )
