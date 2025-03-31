from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis import Redis
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.api.dependencies.database import get_session
from src.api.dependencies.rabbitmq import RabbitMQPublisher
from src.api.dependencies.redis import get_redis
from src.db.models import Base, Role, User
from src.main import app
from src.settings import settings
from src.utils.password_manager import PasswordManager

# Use separate DB for testing
TEST_DATABASE_URL = settings.TEST_DATABASE_URL

# Create async engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,  # Each database connection is opened and closed immediately
    future=True,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


# A fixture for creating a test database before the tests
@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Create tables
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.drop_all
        )  # Delete tables after tests


# A fixture for getting a session
@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(
    session: AsyncSession, mock_redis: Redis
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_redis] = lambda: mock_redis

    transport = ASGITransport(app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(
    session: AsyncSession, password_manager: PasswordManager
) -> AsyncGenerator[User, None]:
    """Create a regular test user."""
    hashed_password = password_manager.get_hash("userpassword")
    user = User(
        name="Regular",
        surname="User",
        username="regular_user",
        email="user@example.com",
        phone_number="+48111222333",
        password=hashed_password,
        role=Role.USER,
        is_blocked=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    yield user


@pytest_asyncio.fixture
async def test_admin(
    session: AsyncSession, password_manager: PasswordManager
) -> AsyncGenerator[User, None]:
    """Create a test admin user."""
    hashed_password = password_manager.get_hash("adminpassword")

    admin = User(
        name="Admin",
        surname="User",
        username="admin_user",
        email="admin@example.com",
        phone_number="+48234567890",
        password=hashed_password,
        role=Role.ADMIN,
        is_blocked=False,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)

    yield admin


@pytest_asyncio.fixture
async def test_moderator(
    session: AsyncSession, password_manager: PasswordManager
) -> AsyncGenerator[User, None]:
    """Create a test moderator user."""
    hashed_password = password_manager.get_hash("moderatorpassword")
    moderator = User(
        name="Moderator",
        surname="User",
        username="moderator_user",
        email="moderator@example.com",
        phone_number="+48987654321",
        password=hashed_password,
        role=Role.MODERATOR,
        is_blocked=False,
    )
    session.add(moderator)
    await session.commit()
    await session.refresh(moderator)

    yield moderator


@pytest_asyncio.fixture
async def user_token_headers(
    client: AsyncClient, test_user: User
) -> AsyncGenerator[dict[str, str], None]:
    """Get token headers for regular user."""
    login_data = {"login": "user@example.com", "password": "userpassword"}
    response = await client.post("/auth/login", json=login_data)

    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())

    tokens = response.json()
    yield {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest_asyncio.fixture
async def admin_token_headers(
    client: AsyncClient, test_admin: User
) -> AsyncGenerator[dict[str, str], None]:
    """Get token headers for admin user."""
    login_data = {
        "login": "admin@example.com",  # Using email for login
        "password": "adminpassword",
    }
    response = await client.post("/auth/login", json=login_data)
    tokens = response.json()
    yield {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest_asyncio.fixture
async def moderator_token_headers(
    client: AsyncClient, test_moderator: User
) -> AsyncGenerator[dict[str, str], None]:
    """Get token headers for moderator user."""
    login_data = {
        "login": "moderator@example.com",
        "password": "moderatorpassword",
    }
    response = await client.post("/auth/login", json=login_data)
    tokens = response.json()
    yield {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest_asyncio.fixture(scope="session")
def password_manager() -> PasswordManager:
    return PasswordManager()


@pytest_asyncio.fixture
async def mock_redis() -> AsyncGenerator[Redis, None]:
    """Mock Redis for authentication tests."""
    redis_mock = AsyncMock(spec=Redis)

    # Mock Redis async methods
    redis_mock.get = AsyncMock(return_value=None)  # Simulate token not found
    redis_mock.setex = AsyncMock(
        return_value=True
    )  # Simulate successful Redis write
    redis_mock.exists = AsyncMock(
        return_value=False
    )  # Simulate token not blacklisted
    redis_mock.delete = AsyncMock(
        return_value=True
    )  # Simulate successful deletion

    yield redis_mock


@pytest_asyncio.fixture
async def mock_rabbitmq(
    monkeypatch: Any,
) -> AsyncGenerator[list[dict[str, str]], None]:
    """Mock RabbitMQ publisher to avoid actual message sending."""
    messages = []

    # Mock the asynchronous publish_message method
    async def mock_publish_message(queue_name: str, message: str) -> None:
        """Mock method to simulate publishing a message."""
        messages.append({"message": message, "queue": queue_name})

    # Mock the asynchronous connect method
    async def mock_connect() -> None:
        """Mock the async connect method to avoid real connection to RabbitMQ."""
        pass

    # Replace the connect and publish_message methods with mocks
    monkeypatch.setattr(RabbitMQPublisher, "connect", mock_connect)
    monkeypatch.setattr(
        RabbitMQPublisher, "publish_message", mock_publish_message
    )

    yield messages
