# settings/test.py
"""
This module defines the test settings for the application.
It includes configuration variables such as APP_NAME, DEBUG, and LOG_LEVEL.
"""
from pydantic_settings import BaseSettings

class TestSettings(BaseSettings):
    """
    Test settings for the application.
    It includes configuration variables such as APP_NAME, DEBUG, and LOG_LEVEL.
    """
    APP_NAME: str = "Lumen Slate AI Microservice - Test"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
