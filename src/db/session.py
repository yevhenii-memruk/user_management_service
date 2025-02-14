from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from . import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
