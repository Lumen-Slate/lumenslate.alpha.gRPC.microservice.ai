"""
gRPC Service Entry Point - Modular Version
This file now imports the modular AI service implementation for better scalability.
"""

# Export the main AIService class from the modular implementation
from app.services.ai_service_main import AIService

# Keep backward compatibility
__all__ = ["AIService"]
