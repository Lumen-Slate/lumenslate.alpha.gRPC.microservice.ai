"""
MinIO client wrapper for document storage operations.

This module provides a wrapper around the MinIO Python client with
connection verification, bucket management, and error handling.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta
from minio import Minio
from minio.error import S3Error, InvalidResponseError
from urllib3.exceptions import MaxRetryError
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


def async_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator for async retry logic with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
            raise last_exception
        return wrapper
    return decorator


class MinIOClientError(Exception):
    """Base exception for MinIO client operations."""
    pass


class MinIOConnectionError(MinIOClientError):
    """Raised when MinIO connection fails."""
    pass


class MinIOBucketError(MinIOClientError):
    """Raised when bucket operations fail."""
    pass


class MinIOClient:
    """
    MinIO client wrapper with connection verification and bucket management.
    
    Provides high-level operations for document storage with proper error
    handling, retry logic, and health checks.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize MinIO client with configuration.
        
        Args:
            config: Optional configuration dictionary. If None, uses environment variables.
        """
        self.config = config or self._load_config_from_env()
        self.client = None
        self.buckets = {
            "documents": self.config.get("bucket", "documents"),
            "temp": "temp",
            "backups": "backups"
        }
        self._initialize_client()
    
    def _load_config_from_env(self) -> Dict[str, Any]:
        """Load MinIO configuration from environment variables."""
        return {
            "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            "access_key": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            "secret_key": os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            "secure": os.getenv("MINIO_SECURE", "false").lower() == "true",
            "region": os.getenv("MINIO_REGION", "us-east-1"),
            "bucket": os.getenv("MINIO_BUCKET", "documents")
        }
    
    def _initialize_client(self):
        """Initialize the MinIO client with configuration."""
        try:
            self.client = Minio(
                endpoint=self.config["endpoint"],
                access_key=self.config["access_key"],
                secret_key=self.config["secret_key"],
                secure=self.config["secure"],
                region=self.config["region"]
            )
            logger.info(f"MinIO client initialized for endpoint: {self.config['endpoint']}")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise MinIOConnectionError(f"Failed to initialize MinIO client: {e}")
    
    async def verify_connection(self) -> bool:
        """
        Verify MinIO server connectivity.
        
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            # Test basic connectivity by listing buckets
            buckets = list(self.client.list_buckets())
            logger.info(f"Successfully connected to MinIO. Found {len(buckets)} buckets.")
            return True
        except (S3Error, InvalidResponseError, MaxRetryError) as e:
            logger.error(f"Failed to connect to MinIO: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during MinIO connection verification: {e}")
            return False
    
    @async_retry(max_retries=3, delay=1.0)
    async def ensure_buckets_exist(self) -> None:
        """
        Create required buckets if they don't exist.
        
        Raises:
            MinIOBucketError: If bucket creation fails after retries.
        """
        try:
            for bucket_purpose, bucket_name in self.buckets.items():
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name, location=self.config["region"])
                    logger.info(f"Created bucket '{bucket_name}' for {bucket_purpose}")
                else:
                    logger.debug(f"Bucket '{bucket_name}' already exists")
        except S3Error as e:
            error_msg = f"Failed to ensure buckets exist: {e}"
            logger.error(error_msg)
            raise MinIOBucketError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during bucket creation: {e}"
            logger.error(error_msg)
            raise MinIOBucketError(error_msg)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of MinIO service.
        
        Returns:
            Dict containing health status and details.
        """
        health_status = {
            "status": "healthy",
            "endpoint": self.config["endpoint"],
            "buckets": {},
            "errors": []
        }
        
        try:
            # Check connection
            if not await self.verify_connection():
                health_status["status"] = "unhealthy"
                health_status["errors"].append("Connection verification failed")
                return health_status
            
            # Check bucket accessibility
            for bucket_purpose, bucket_name in self.buckets.items():
                try:
                    exists = self.client.bucket_exists(bucket_name)
                    health_status["buckets"][bucket_name] = {
                        "exists": exists,
                        "purpose": bucket_purpose
                    }
                    if not exists:
                        health_status["errors"].append(f"Bucket '{bucket_name}' does not exist")
                except Exception as e:
                    health_status["buckets"][bucket_name] = {
                        "exists": False,
                        "error": str(e),
                        "purpose": bucket_purpose
                    }
                    health_status["errors"].append(f"Failed to check bucket '{bucket_name}': {e}")
            
            if health_status["errors"]:
                health_status["status"] = "degraded"
                
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["errors"].append(f"Health check failed: {e}")
        
        return health_status
    
    def get_presigned_url(self, bucket_name: str, object_name: str, 
                         expires: timedelta = timedelta(minutes=30)) -> str:
        """
        Generate a presigned URL for object access.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            expires: URL expiration time (default: 30 minutes)
            
        Returns:
            str: Presigned URL
            
        Raises:
            MinIOClientError: If URL generation fails
        """
        try:
            url = self.client.presigned_get_object(bucket_name, object_name, expires=expires)
            logger.debug(f"Generated presigned URL for {bucket_name}/{object_name}")
            return url
        except S3Error as e:
            error_msg = f"Failed to generate presigned URL for {bucket_name}/{object_name}: {e}"
            logger.error(error_msg)
            raise MinIOClientError(error_msg)
    
    def list_objects(self, bucket_name: str, prefix: str = "", recursive: bool = True) -> List[Dict[str, Any]]:
        """
        List objects in a bucket with optional prefix filtering.
        
        Args:
            bucket_name: Name of the bucket
            prefix: Object name prefix filter
            recursive: Whether to list recursively
            
        Returns:
            List of object information dictionaries
            
        Raises:
            MinIOClientError: If listing fails
        """
        try:
            objects = []
            for obj in self.client.list_objects(bucket_name, prefix=prefix, recursive=recursive):
                objects.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag,
                    "content_type": getattr(obj, 'content_type', None)
                })
            return objects
        except S3Error as e:
            error_msg = f"Failed to list objects in {bucket_name}: {e}"
            logger.error(error_msg)
            raise MinIOClientError(error_msg)
    
    async def initialize_service(self) -> None:
        """
        Initialize the MinIO service by verifying connection and creating buckets.
        
        This method should be called during application startup.
        
        Raises:
            MinIOConnectionError: If connection verification fails
            MinIOBucketError: If bucket initialization fails
        """
        logger.info("Initializing MinIO service...")
        
        # Verify connection
        if not await self.verify_connection():
            raise MinIOConnectionError("Failed to verify MinIO connection during initialization")
        
        # Ensure required buckets exist
        await self.ensure_buckets_exist()
        
        logger.info("MinIO service initialization completed successfully")
    
    def get_client_config(self) -> Dict[str, Any]:
        """
        Get the current client configuration (without sensitive data).
        
        Returns:
            Dict containing non-sensitive configuration information.
        """
        return {
            "endpoint": self.config["endpoint"],
            "secure": self.config["secure"],
            "region": self.config["region"],
            "bucket": self.config["bucket"],
            "buckets": self.buckets
        }


# Global MinIO client instance
_minio_client: Optional[MinIOClient] = None


def get_minio_client() -> MinIOClient:
    """
    Get the global MinIO client instance.
    
    Returns:
        MinIOClient: The global MinIO client instance.
    """
    global _minio_client
    if _minio_client is None:
        _minio_client = MinIOClient()
    return _minio_client


async def initialize_minio() -> None:
    """
    Initialize the global MinIO client and service.
    
    This function should be called during application startup.
    """
    client = get_minio_client()
    await client.initialize_service()


# Export main classes and functions
__all__ = [
    'MinIOClient',
    'MinIOClientError', 
    'MinIOConnectionError',
    'MinIOBucketError',
    'get_minio_client',
    'initialize_minio'
]