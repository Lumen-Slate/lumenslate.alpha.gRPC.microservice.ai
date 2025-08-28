"""
Service Factory for creating AI service instances.
Provides a clean interface for service instantiation and configuration.
"""

import logging
from app.router.grpc_micro_service import GRPCAIMicroService
from app.config.logging_config import logger


class ServiceFactory:
    """Factory class for creating AI service instances"""

    @staticmethod
    def create_ai_service(custom_logger=None):
        """
        Create an AIService instance with optional custom logger.

        Args:
            custom_logger: Optional custom logger instance

        Returns:
            AIService: Configured AI service instance
        """
        service_logger = custom_logger or logger
        return GRPCAIMicroService(service_logger)

    @staticmethod
    def create_ai_service_with_config(log_level=None, log_format=None):
        """
        Create an AIService instance with custom logging configuration.

        Args:
            log_level: Optional custom log level
            log_format: Optional custom log format

        Returns:
            AIService: Configured AI service instance
        """
        if log_level or log_format:
            custom_logger = logging.getLogger("ai_service_custom")
            if log_level:
                custom_logger.setLevel(getattr(logging, log_level.upper()))

            if log_format:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(log_format)
                handler.setFormatter(formatter)
                custom_logger.addHandler(handler)

            return GRPCAIMicroService(custom_logger)
        else:
            return ServiceFactory.create_ai_service()


# Convenience function for backward compatibility
def get_ai_service(logger_instance=None):
    """
    Get an AIService instance (backward compatibility function).

    Args:
        logger_instance: Optional logger instance

    Returns:
        AIService: Configured AI service instance
    """
    return ServiceFactory.create_ai_service(logger_instance)
