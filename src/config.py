from pydantic_settings import BaseSettings, SettingsConfigDict

# from pathlib import Path

# base_dir = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="/opt/project/.env")
    # model_config = SettingsConfigDict(env_file=base_dir / ".env")

    PROJECT_NAME: str = "User Management Service"
    DEBUG: bool
    LOG_LEVEL: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_NAME: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASS: str

    # RabbitMQ
    RABBITMQ_USER: str
    RABBITMQ_PASS: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int


settings = Settings()

# print(settings.model_dump())
