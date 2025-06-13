"""
This module initializes the settings for the application based on the environment.
It imports the appropriate settings class (DevSettings, TestSettings, ProdSettings)
depending on the value of the ENV environment variable.
"""

import os
from app.config.settings.dev import DevSettings
from app.config.settings.test import TestSettings
from app.config.settings.prod import ProdSettings

ENV = os.getenv("ENV", "dev")

if ENV == "dev":
    settings = DevSettings()
elif ENV == "test":
    settings = TestSettings()
elif ENV == "prod":
    settings = ProdSettings()
else:
    settings = DevSettings()
