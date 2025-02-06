import logging
import sys
from logging.config import dictConfig

from config import settings


def configure_logger():
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - [%(levelname)s] \
                - %(name)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "level": settings.LOG_LEVEL,
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": sys.stdout,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console"],
        },
    }
    dictConfig(log_config)


configure_logger()
logger = logging.getLogger("ums")

logger.info("Logging configured.")
