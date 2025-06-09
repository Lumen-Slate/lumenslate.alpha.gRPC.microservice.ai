# settings/prod.py
"""
This module defines the production settings for the application.
It includes configuration variables such as APP_NAME, DEBUG, and LOG_LEVEL.
"""
from pydantic_settings import BaseSettings

class ProdSettings(BaseSettings):
    """
    Production settings for the application.
    It includes configuration variables such as APP_NAME, DEBUG, and LOG_LEVEL.
    """
    APP_NAME: str = "Lumen Slate AI Microservice - Prod"
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
