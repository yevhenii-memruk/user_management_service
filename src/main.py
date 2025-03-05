import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import auth, health, user
from src.logger import configure_logger
from src.settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logger()
    yield  # app starts
    logger.info("App shutdown")


app = FastAPI(lifespan=lifespan, title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(health.router)


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to User Management Microservice",
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
