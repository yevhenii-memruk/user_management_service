import logging

from fastapi import APIRouter

router = APIRouter(tags=["health"])

logger = logging.getLogger(f"ums.{__name__}")


@router.get("/")
async def root() -> dict[str, str]:
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to User Management Microservice",
        "docs": "/docs",
        "redoc": "/redoc",
    }
