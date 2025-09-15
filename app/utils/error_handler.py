"""
Error handling utilities for Document Service.

This module provides structured error handling, retry logic, and circuit breaker
patterns for MinIO and database operations.
"""

import asyncio
import logging
from typing import Callable, Any, Optional, Dict
from functools import wraps
from datetime import datetime, timedelta
import grpc
from grpc import StatusCode

from app.protos.document_service_pb2 import ErrorDetails, ValidationError as ProtoValidationError

logger = logging.getLogger(__name__)


class DocumentServiceError(Exception):
    """Base exception for Document Service operations."""
    
    def __init__(self, code: grpc.StatusCode, message: str, details: Dict[str, str] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def to_grpc_error_details(self) -> ErrorDetails:
        """Convert to gRPC ErrorDetails message."""
        return ErrorDetails(
            error_code=self.code.name,
            error_message=self.message,
            details=self.details
        )


class ValidationError(DocumentServiceError):
    """Raised when document validation fails."""
    
    def __init__(self, field: str, message: str, rejected_value: str = ""):
        super().__init__(
            grpc.StatusCode.INVALID_ARGUMENT,
            f"Validation failed for {field}: {message}",
            {"field": field, "rejected_value": rejected_value}
        )
        self.field = field
        self.rejected_value = rejected_value
    
    def to_proto_validation_error(self) -> ProtoValidationError:
        """Convert to gRPC ValidationError message."""
        return ProtoValidationError(
            field=self.field,
            message=self.message,
            rejected_value=self.rejected_value
        )


class QuotaExceededError(DocumentServiceError):
    """Raised when user storage quota is exceeded."""
    
    def __init__(self, current_usage: int, limit: int):
        super().__init__(
            grpc.StatusCode.RESOURCE_EXHAUSTED,
            f"Storage quota exceeded: {current_usage}/{limit} bytes",
            {"current_usage": str(current_usage), "limit": str(limit)}
        )


class MinIOUnavailableError(DocumentServiceError):
    """Raised when MinIO service is unavailable."""
    
    def __init__(self, operation: str, original_error: str):
        super().__init__(
            grpc.StatusCode.UNAVAILABLE,
            f"MinIO unavailable for {operation}: {original_error}",
            {"operation": operation, "original_error": original_error}
        )


class DatabaseUnavailableError(DocumentServiceError):
    """Raised when database is unavailable."""
    
    def __init__(self, operation: str, original_error: str):
        super().__init__(
            grpc.StatusCode.UNAVAILABLE,
            f"Database unavailable for {operation}: {original_error}",
            {"operation": operation, "original_error": original_error}
        )


class DocumentNotFoundError(DocumentServiceError):
    """Raised when document is not found."""
    
    def __init__(self, document_id: str):
        super().__init__(
            grpc.StatusCode.NOT_FOUND,
            f"Document not found: {document_id}",
            {"document_id": document_id}
        )


class PermissionDeniedError(DocumentServiceError):
    """Raised when user doesn't have permission to access document."""
    
    def __init__(self, user_id: str, document_id: str):
        super().__init__(
            grpc.StatusCode.PERMISSION_DENIED,
            f"User {user_id} does not have permission to access document {document_id}",
            {"user_id": user_id, "document_id": document_id}
        )


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for external service calls.
    
    Prevents cascading failures by temporarily disabling calls to failing services.
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset."""
        if self.state == "OPEN" and self.last_failure_time:
            return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        return False
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            DocumentServiceError: If circuit is open or function fails
        """
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker attempting reset")
            else:
                raise DocumentServiceError(
                    grpc.StatusCode.UNAVAILABLE,
                    "Service temporarily unavailable (circuit breaker open)"
                )
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Success - reset circuit breaker
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("Circuit breaker reset to CLOSED")
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise e


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")
            
            raise last_exception
        return wrapper
    return decorator


class ErrorHandler:
    """
    Centralized error handler for Document Service operations.
    
    Provides consistent error handling, logging, and metrics collection.
    """
    
    def __init__(self):
        """Initialize error handler."""
        self.minio_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self.database_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
    
    async def handle_minio_operation(self, operation: str, func: Callable, *args, **kwargs) -> Any:
        """
        Handle MinIO operations with circuit breaker and error handling.
        
        Args:
            operation: Operation name for logging
            func: MinIO operation function
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Operation result
            
        Raises:
            MinIOUnavailableError: If MinIO is unavailable
        """
        try:
            return await self.minio_circuit_breaker.call(func, *args, **kwargs)
        except Exception as e:
            logger.error(f"MinIO operation '{operation}' failed: {e}")
            raise MinIOUnavailableError(operation, str(e))
    
    async def handle_database_operation(self, operation: str, func: Callable, *args, **kwargs) -> Any:
        """
        Handle database operations with circuit breaker and error handling.
        
        Args:
            operation: Operation name for logging
            func: Database operation function
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Operation result
            
        Raises:
            DatabaseUnavailableError: If database is unavailable
        """
        try:
            return await self.database_circuit_breaker.call(func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Database operation '{operation}' failed: {e}")
            raise DatabaseUnavailableError(operation, str(e))
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """
        Get current circuit breaker status for monitoring.
        
        Returns:
            Dict containing circuit breaker status information
        """
        return {
            "minio": {
                "state": self.minio_circuit_breaker.state,
                "failure_count": self.minio_circuit_breaker.failure_count,
                "last_failure": self.minio_circuit_breaker.last_failure_time.isoformat() 
                    if self.minio_circuit_breaker.last_failure_time else None
            },
            "database": {
                "state": self.database_circuit_breaker.state,
                "failure_count": self.database_circuit_breaker.failure_count,
                "last_failure": self.database_circuit_breaker.last_failure_time.isoformat()
                    if self.database_circuit_breaker.last_failure_time else None
            }
        }


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Get the global error handler instance.
    
    Returns:
        ErrorHandler: The global error handler instance
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


# Utility functions for common error scenarios
def validate_user_id(user_id: str) -> None:
    """Validate user ID format."""
    if not user_id or not user_id.strip():
        raise ValidationError("user_id", "User ID is required")


def validate_document_id(document_id: str) -> None:
    """Validate document ID format."""
    if not document_id or not document_id.strip():
        raise ValidationError("document_id", "Document ID is required")


def validate_filename(filename: str) -> None:
    """Validate filename format."""
    if not filename or not filename.strip():
        raise ValidationError("filename", "Filename is required")
    
    if len(filename) > 255:
        raise ValidationError("filename", "Filename too long (max 255 characters)", filename)
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in filename:
            raise ValidationError("filename", f"Filename contains invalid character: {char}", filename)