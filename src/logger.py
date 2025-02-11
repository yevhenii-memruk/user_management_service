import logging
import sys
from logging.config import dictConfig
# from logging.handlers import RotatingFileHandler

from src.settings import settings

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - [%(levelname)s]"
            "- %(name)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": settings.LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": sys.stdout,
        },
        "file": {
            "level": settings.LOG_LEVEL,
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": "logs/app.log",
            "mode": "a",
            "maxBytes": 5 * 1024 * 1024,  # 5MB limit
            "backupCount": 3,
        },
    },
    "root": {
        "level": settings.LOG_LEVEL,
        "handlers": ["console", "file"],
    },
}


def configure_logger() -> None:
    dictConfig(logging_config)
    logger = logging.getLogger("ums")
    logger.info("Logging configured.")
