import logging

from fastapi import APIRouter

from src.schemas.health import HealthCheckResponse

logger = logging.getLogger(f"ums.{__name__}")
router = APIRouter()


@router.get("/")
async def healthcheck() -> HealthCheckResponse:
    logger.info("Healthcheck endpoint accessed")

    return HealthCheckResponse(message="ok")
