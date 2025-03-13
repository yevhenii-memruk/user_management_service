from typing import Literal, TypeAlias

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel: TypeAlias = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_dotenv(".env", raise_error_if_not_found=True)
    )

    PROJECT_NAME: str = "User Management Service"
    DEBUG: bool = False
    LOG_LEVEL: LogLevel = "INFO"
    LOG_DIR: str = "logs"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30 * 60
    JWT_EXPIRE_DAYS: int = 7
    JWT_SECRET_KEY: str

    # PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_NAME: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    # RabbitMQ
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int

    # Frontend URL for generating reset links
    FRONTEND_URL: str

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_NAME}"
        )


settings = Settings()
