"""
This module configures the logging for the application.
It sets the log level, format, and handlers based on the application settings.
"""

import logging
import sys
from config.settings import settings

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("ai_microservice.log", mode='a')
    ]
)

logger = logging.getLogger(settings.APP_NAME)
