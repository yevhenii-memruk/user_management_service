from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import async_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async SQLAlchemy session.
    """
    async with async_session() as session:
        yield session
