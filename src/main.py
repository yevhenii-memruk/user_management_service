import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI

from src.logger import configure_logger
from src.schemas.health import HealthCheckResponse
from src.settings import settings

configure_logger()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("App startup")
    yield  # app starts
    logger.info("App shutdown")


app = FastAPI(lifespan=lifespan, title=settings.PROJECT_NAME)


@app.get("/healthcheck", response_model=HealthCheckResponse)
async def healthcheck() -> HealthCheckResponse:
    logger.info("Healthcheck")
    return HealthCheckResponse(message="OK")


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
