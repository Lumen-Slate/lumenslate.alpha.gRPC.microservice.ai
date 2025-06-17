"""
Services module for AI microservice.
Contains modular service implementations for better scalability and maintainability.
"""

from app.services.ai_service_main import AIService
from app.services.service_factory import ServiceFactory, get_ai_service
from app.services.base_service import BaseService
from app.services.question_generation_service import QuestionGenerationService
from app.services.agent_service import AgentService
from app.services.corpus_management_service import CorpusManagementService
from app.services.data_access_service import DataAccessService

__all__ = [
    "AIService",
    "ServiceFactory", 
    "get_ai_service",
    "BaseService",
    "QuestionGenerationService",
    "AgentService", 
    "CorpusManagementService",
    "DataAccessService"
]
