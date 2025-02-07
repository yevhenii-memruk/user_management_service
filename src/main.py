from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from src.logger import configure_logger, logger
from src.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logger()
    logger.info("success: Logger configured.")
    yield  # app starts
    logger.info("Shutting down.")


app = FastAPI(lifespan=lifespan, title=settings.PROJECT_NAME)


class HealthCheckResponse(BaseModel):
    message: str


@app.get("/healthcheck", response_model=HealthCheckResponse)
async def healthcheck() -> HealthCheckResponse:
    logger.info("Healthcheck")
    return HealthCheckResponse(message="OK")


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
