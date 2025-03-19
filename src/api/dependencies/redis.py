from typing import AsyncGenerator

from redis.asyncio import Redis

from src.settings import settings


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Dependency for getting Redis connection.
    """
    redis_client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,  # Ensures results are returned as strings
    )
    try:
        yield redis_client
    finally:
        await redis_client.close()
