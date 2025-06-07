"""
This module defines the settings for the application.
It includes configuration variables such as APP_NAME, HOST, PORT, and DEBUG,
and selects the appropriate settings based on the environment.
"""
import os
from pydantic_settings import BaseSettings
from config.settings import dev, test, prod

class Settings(BaseSettings):
    """
    Settings class for the application.
    It includes configuration variables such as APP_NAME, HOST, PORT, and DEBUG.
    """
    APP_NAME: str
    HOST: str
    PORT: int
    DEBUG: bool

    class Config:
        """
        Configuration for the Settings class.
        Specifies the environment file to be used.
        """
        env_file = "../.env"


ENV = os.getenv("ENV", "dev")
if ENV == "dev":
    settings = dev.DevSettings()
elif ENV == "test":
    settings = test.TestSettings()
elif ENV == "prod":
    settings = prod.ProdSettings()
else:
    settings = dev.DevSettings()
