"""
This module configures the logging for the application.
It sets the log level, format, and handlers based on the application settings.
Ensures compatibility with gRPC logging.
"""

import logging
import sys
from app.config.settings import settings

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

# Remove all handlers associated with the root logger object (to avoid duplicate logs)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("ai_microservice.log", mode='a')
    ]
)

logger = logging.getLogger(settings.APP_NAME)

# Ensure gRPC logs are also handled by our logger
logging.getLogger('grpc').setLevel(getattr(logging, settings.LOG_LEVEL))
logging.getLogger('grpc').addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger('grpc').addHandler(logging.FileHandler("ai_microservice.log", mode='a'))
