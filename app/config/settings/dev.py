"""
This module defines the development settings for the application.
It includes configuration variables such as APP_NAME, DEBUG, and LOG_LEVEL.
"""
from pydantic_settings import BaseSettings

class DevSettings(BaseSettings):
    """
    Development settings for the application.
    It includes configuration variables such as APP_NAME, DEBUG, and LOG_LEVEL.
    """
    APP_NAME: str = "Lumen Slate AI Microservice - Dev"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
