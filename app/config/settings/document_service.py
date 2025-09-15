"""
Document Service configuration settings.
This module provides configuration for the Document Storage Service using Prisma ORM.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class DocumentServiceSettings(BaseSettings):
    """
    Configuration settings for the Document Storage Service.
    Follows the existing LumenSlate configuration pattern.
    """
    
    # Database Configuration (Prisma)
    microservice_database: str = os.getenv("MICROSERVICE_DATABASE", "mysql://root:password@localhost:3306/lumenslate")
    
    # MinIO Configuration (Self-Hosted Open Source)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"  # Maps to MINIO_ROOT_USER
    minio_secret_key: str = "minioadmin"  # Maps to MINIO_ROOT_PASSWORD
    minio_secure: bool = False
    minio_region: str = "us-east-1"
    minio_bucket: str = "documents"
    
    # Storage Backend Configuration
    storage_backend: str = "minio"
    storage_max_file_size: str = "50MB"
    storage_allowed_extensions: List[str] = ["pdf", "doc", "docx", "txt", "xlsx"]
    
    # Service Configuration
    max_file_size: int = 52428800  # 50MB in bytes
    allowed_mime_types: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain"
    ]
    
    # Quota Configuration
    default_user_quota: int = 1073741824  # 1GB in bytes
    
    # Monitoring Configuration
    metrics_port: int = 9100
    
    # MinIO Console
    minio_console_endpoint: str = "localhost:9001"
    
    # Prisma Configuration
    prisma_auto_connect: bool = True
    prisma_connection_timeout: int = 30  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables
        
    @property
    def minio_client_config(self) -> dict:
        """
        MinIO client configuration dictionary.
        
        Returns:
            dict: MinIO client configuration
        """
        return {
            "endpoint": self.minio_endpoint,
            "access_key": self.minio_access_key,
            "secret_key": self.minio_secret_key,
            "secure": self.minio_secure,
            "region": self.minio_region
        }
    
    @property
    def max_file_size_bytes(self) -> int:
        """
        Get maximum file size in bytes.
        
        Returns:
            int: Maximum file size in bytes
        """
        return self.max_file_size
    
    def is_allowed_mime_type(self, mime_type: str) -> bool:
        """
        Check if a MIME type is allowed.
        
        Args:
            mime_type: MIME type to check
            
        Returns:
            bool: True if allowed, False otherwise
        """
        return mime_type in self.allowed_mime_types
    
    def is_allowed_file_extension(self, filename: str) -> bool:
        """
        Check if a file extension is allowed.
        
        Args:
            filename: Filename to check
            
        Returns:
            bool: True if allowed, False otherwise
        """
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in self.storage_allowed_extensions

# Global settings instance
document_service_settings = DocumentServiceSettings()