from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.db.models import Group
from src.settings import settings

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


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get DB session for test."""
    async with TestingSessionLocal() as session:
        yield session
        # Roll back changes after each test
        await session.rollback()


@pytest_asyncio.fixture
async def test_group(db_session) -> Group:
    """Fixture to create a test group."""
    group = Group(name="Test Group")
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)
    return group
