"""
Services module for AI microservice.
Contains modular service implementations for better scalability and maintainability.
"""

from app.services.ai_service_main import AIService
from app.services.service_factory import ServiceFactory, get_ai_service
from app.services.base_service import BaseService
from app.services.independent_agent_service import IndependentAgentService
from app.services.orchestrated_agent_service import OrchestratedAgentService
from app.services.rag_corpus_management_service import RAGCorpusManagementService
from app.services.data_access_service import DataAccessService

__all__ = [
    "AIService",
    "ServiceFactory", 
    "get_ai_service",
    "BaseService",
    "IndependentAgentService",
    "OrchestratedAgentService", 
    "RAGCorpusManagementService",
    "DataAccessService"
]
