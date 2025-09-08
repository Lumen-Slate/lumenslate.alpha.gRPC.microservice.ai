import os
from google.adk.sessions import DatabaseSessionService, InMemorySessionService


class SessionServiceManager:
    """
    Manages and provides access to both DatabaseSessionService and InMemorySessionService.
    Instantiated once at server startup and imported wherever needed.
    """

    def __init__(self):
        self.database_session_service = DatabaseSessionService(
            db_url=os.getenv("MICROSERVICE_DATABASE"),
            connect_args={"ssl": {"ca": os.getenv("MICROSERVICE_DATABASE_CA")}}
        )
        self.inmemory_session_service = InMemorySessionService()

    def get_database_service(self):
        return self.database_session_service

    def get_inmemory_service(self):
        return self.inmemory_session_service


# Instantiate globally for import
session_service_manager = SessionServiceManager()
