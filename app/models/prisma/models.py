"""
Prisma database models and operations for Document Storage Service.
This module provides type-safe database operations using Prisma ORM.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from prisma import Prisma
from prisma.models import Document, UserUsage
from prisma.enums import Status
from prisma.errors import PrismaError
import logging

logger = logging.getLogger(__name__)

class DocumentRepository:
    """
    Repository class for Document model operations using Prisma.
    Provides CRUD operations and business logic for document management.
    """
    
    def __init__(self, prisma_client: Prisma):
        self.client = prisma_client
    
    async def create_document(
        self,
        user_id: str,
        category: str,
        filename: str,
        path: str,
        size: int,
        mime_type: str,
        status: Status = Status.PENDING
    ) -> Document:
        """
        Create a new document record.
        
        Args:
            user_id: User identifier
            category: Document category
            filename: Original filename
            path: Storage path in MinIO
            size: File size in bytes
            mime_type: MIME type of the file
            status: Document processing status
            
        Returns:
            Document: Created document record
            
        Raises:
            PrismaError: If database operation fails
        """
        try:
            document = await self.client.document.create(
                data={
                    'userId': user_id,
                    'category': category,
                    'filename': filename,
                    'path': path,
                    'size': size,
                    'mimeType': mime_type,
                    'status': status
                }
            )
            logger.info(f"Created document record: {document.id} for user {user_id}")
            return document
        except PrismaError as e:
            logger.error(f"Failed to create document record: {e}")
            raise
    
    async def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """
        Retrieve a document by its ID.
        
        Args:
            document_id: Document UUID
            
        Returns:
            Document: Document record if found, None otherwise
        """
        try:
            document = await self.client.document.find_unique(
                where={'id': document_id}
            )
            return document
        except PrismaError as e:
            logger.error(f"Failed to retrieve document {document_id}: {e}")
            raise
    
    async def get_document_by_path(self, path: str) -> Optional[Document]:
        """
        Retrieve a document by its storage path.
        
        Args:
            path: Storage path in MinIO
            
        Returns:
            Document: Document record if found, None otherwise
        """
        try:
            document = await self.client.document.find_unique(
                where={'path': path}
            )
            return document
        except PrismaError as e:
            logger.error(f"Failed to retrieve document by path {path}: {e}")
            raise
    
    async def list_documents_by_user(
        self,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """
        List documents for a specific user with optional filtering.
        
        Args:
            user_id: User identifier
            category: Optional category filter
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List[Document]: List of document records
        """
        try:
            where_clause = {'userId': user_id}
            if category:
                where_clause['category'] = category
            
            documents = await self.client.document.find_many(
                where=where_clause,
                order={'createdAt': 'desc'},
                take=limit,
                skip=offset
            )
            return documents
        except PrismaError as e:
            logger.error(f"Failed to list documents for user {user_id}: {e}")
            raise
    
    async def update_document_status(self, document_id: str, status: Status) -> Optional[Document]:
        """
        Update the status of a document.
        
        Args:
            document_id: Document UUID
            status: New status
            
        Returns:
            Document: Updated document record if found, None otherwise
        """
        try:
            document = await self.client.document.update(
                where={'id': document_id},
                data={'status': status}
            )
            logger.info(f"Updated document {document_id} status to {status}")
            return document
        except PrismaError as e:
            logger.error(f"Failed to update document {document_id} status: {e}")
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document record.
        
        Args:
            document_id: Document UUID
            
        Returns:
            bool: True if deleted successfully, False if not found
        """
        try:
            await self.client.document.delete(
                where={'id': document_id}
            )
            logger.info(f"Deleted document record: {document_id}")
            return True
        except PrismaError as e:
            if "Record to delete does not exist" in str(e):
                logger.warning(f"Document {document_id} not found for deletion")
                return False
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise
    
    async def get_user_document_count(self, user_id: str) -> int:
        """
        Get the total number of documents for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            int: Number of documents
        """
        try:
            count = await self.client.document.count(
                where={'userId': user_id}
            )
            return count
        except PrismaError as e:
            logger.error(f"Failed to count documents for user {user_id}: {e}")
            raise
    
    async def get_user_storage_size(self, user_id: str) -> int:
        """
        Calculate total storage size for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            int: Total storage size in bytes
        """
        try:
            # Use aggregation to sum file sizes
            result = await self.client.document.aggregate(
                where={'userId': user_id},
                _sum={'size': True}
            )
            return result['_sum']['size'] or 0
        except PrismaError as e:
            logger.error(f"Failed to calculate storage size for user {user_id}: {e}")
            raise

class UserUsageRepository:
    """
    Repository class for UserUsage model operations using Prisma.
    Provides operations for tracking user storage statistics.
    """
    
    def __init__(self, prisma_client: Prisma):
        self.client = prisma_client
    
    async def get_user_usage(self, user_id: str) -> Optional[UserUsage]:
        """
        Get usage statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserUsage: Usage record if found, None otherwise
        """
        try:
            usage = await self.client.userusage.find_unique(
                where={'userId': user_id}
            )
            return usage
        except PrismaError as e:
            logger.error(f"Failed to retrieve usage for user {user_id}: {e}")
            raise
    
    async def create_or_update_usage(
        self,
        user_id: str,
        file_count_delta: int = 0,
        bytes_delta: int = 0
    ) -> UserUsage:
        """
        Create or update user usage statistics atomically.
        
        Args:
            user_id: User identifier
            file_count_delta: Change in file count (can be negative)
            bytes_delta: Change in bytes (can be negative)
            
        Returns:
            UserUsage: Updated usage record
        """
        try:
            # Use upsert to handle both create and update cases
            usage = await self.client.userusage.upsert(
                where={'userId': user_id},
                data={
                    'create': {
                        'userId': user_id,
                        'fileCount': file_count_delta,
                        'totalBytes': bytes_delta
                    },
                    'update': {
                        'fileCount': {'increment': file_count_delta},
                        'totalBytes': {'increment': bytes_delta}
                    }
                }
            )
            logger.info(f"Updated usage for user {user_id}: files={usage.fileCount}, bytes={usage.totalBytes}")
            return usage
        except PrismaError as e:
            logger.error(f"Failed to update usage for user {user_id}: {e}")
            raise
    
    async def reset_user_usage(self, user_id: str) -> UserUsage:
        """
        Reset user usage statistics to zero.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserUsage: Reset usage record
        """
        try:
            usage = await self.client.userusage.upsert(
                where={'userId': user_id},
                data={
                    'create': {
                        'userId': user_id,
                        'fileCount': 0,
                        'totalBytes': 0
                    },
                    'update': {
                        'fileCount': 0,
                        'totalBytes': 0
                    }
                }
            )
            logger.info(f"Reset usage for user {user_id}")
            return usage
        except PrismaError as e:
            logger.error(f"Failed to reset usage for user {user_id}: {e}")
            raise
    
    async def get_all_usage_stats(self) -> List[UserUsage]:
        """
        Get usage statistics for all users.
        
        Returns:
            List[UserUsage]: List of all usage records
        """
        try:
            usage_records = await self.client.userusage.find_many(
                order={'totalBytes': 'desc'}
            )
            return usage_records
        except PrismaError as e:
            logger.error(f"Failed to retrieve all usage stats: {e}")
            raise

class DocumentService:
    """
    High-level service class that combines Document and UserUsage operations.
    Provides transactional operations that maintain consistency between models.
    """
    
    def __init__(self, prisma_client: Prisma):
        self.client = prisma_client
        self.document_repo = DocumentRepository(prisma_client)
        self.usage_repo = UserUsageRepository(prisma_client)
    
    async def create_document_with_usage_update(
        self,
        user_id: str,
        category: str,
        filename: str,
        path: str,
        size: int,
        mime_type: str
    ) -> Document:
        """
        Create a document and update user usage statistics in a transaction.
        
        Args:
            user_id: User identifier
            category: Document category
            filename: Original filename
            path: Storage path in MinIO
            size: File size in bytes
            mime_type: MIME type of the file
            
        Returns:
            Document: Created document record
        """
        try:
            # Use Prisma transaction to ensure consistency
            async with self.client.tx() as transaction:
                # Create document
                document = await transaction.document.create(
                    data={
                        'userId': user_id,
                        'category': category,
                        'filename': filename,
                        'path': path,
                        'size': size,
                        'mimeType': mime_type,
                        'status': Status.PENDING
                    }
                )
                
                # Update usage statistics
                await transaction.userusage.upsert(
                    where={'userId': user_id},
                    data={
                        'create': {
                            'userId': user_id,
                            'fileCount': 1,
                            'totalBytes': size
                        },
                        'update': {
                            'fileCount': {'increment': 1},
                            'totalBytes': {'increment': size}
                        }
                    }
                )
                
                logger.info(f"Created document {document.id} and updated usage for user {user_id}")
                return document
                
        except PrismaError as e:
            logger.error(f"Failed to create document with usage update: {e}")
            raise
    
    async def delete_document_with_usage_update(self, document_id: str) -> bool:
        """
        Delete a document and update user usage statistics in a transaction.
        
        Args:
            document_id: Document UUID
            
        Returns:
            bool: True if deleted successfully, False if not found
        """
        try:
            # First get the document to know the user and size
            document = await self.document_repo.get_document_by_id(document_id)
            if not document:
                return False
            
            # Use transaction to ensure consistency
            async with self.client.tx() as transaction:
                # Delete document
                await transaction.document.delete(
                    where={'id': document_id}
                )
                
                # Update usage statistics
                await transaction.userusage.update(
                    where={'userId': document.userId},
                    data={
                        'fileCount': {'decrement': 1},
                        'totalBytes': {'decrement': document.size}
                    }
                )
                
                logger.info(f"Deleted document {document_id} and updated usage for user {document.userId}")
                return True
                
        except PrismaError as e:
            if "Record to delete does not exist" in str(e):
                logger.warning(f"Document {document_id} not found for deletion")
                return False
            logger.error(f"Failed to delete document with usage update: {e}")
            raise