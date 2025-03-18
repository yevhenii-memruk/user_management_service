import logging

from fastapi import APIRouter

from src.schemas.root import RootResponse

logger = logging.getLogger(f"ums.{__name__}")

router = APIRouter()


@router.get("/")
async def root() -> RootResponse:
    logger.info("Root endpoint accessed")
    return RootResponse(
        message="Welcome to User Management Microservice",
        docs="/docs",
        redoc="/redoc",
    )
