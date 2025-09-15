"""
Document Service implementation for user document storage and management.

This service provides gRPC-based document operations including upload, download,
deletion, listing, and usage statistics with MinIO storage and Prisma ORM.
"""

import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import AsyncIterator, Optional, List, Dict, Any
import grpc
from grpc import StatusCode

# Import generated gRPC classes
from app.protos.document_service_pb2 import (
    UploadDocumentRequest, UploadDocumentResponse,
    DownloadDocumentRequest, DownloadDocumentResponse,
    DeleteDocumentRequest, DeleteDocumentResponse,
    ListDocumentsRequest, ListDocumentsResponse,
    GetDocumentUrlRequest, GetDocumentUrlResponse,
    GetUsageStatsRequest, GetUsageStatsResponse,
    DocumentInfo, DocumentSummary, UsageStats, QuotaInfo,
    ErrorDetails, ValidationError
)
from app.protos.document_service_pb2_grpc import DocumentServiceServicer

# Import dependencies
from app.models.prisma import get_prisma_client
from app.utils.minio_client import get_minio_client, MinIOClientError
from app.config.settings.document_service import document_service_settings
from app.utils.error_handler import (
    get_error_handler, DocumentServiceError, QuotaExceededError,
    ValidationError as ServiceValidationError, MinIOUnavailableError,
    DatabaseUnavailableError, DocumentNotFoundError, PermissionDeniedError,
    validate_user_id, validate_document_id, validate_filename,
    retry_with_backoff
)
from app.utils.metrics_collector import (
    get_metrics_collector, record_upload_success, record_download_success,
    record_delete_success, record_quota_exceeded, record_minio_unavailable,
    record_database_unavailable, record_operation_failure
)
from prisma.errors import PrismaError

logger = logging.getLogger(__name__)





class DocumentService(DocumentServiceServicer):
    """
    gRPC Document Service implementation.
    
    Provides document storage operations with MinIO backend and Prisma ORM
    for metadata management.
    """
    
    def __init__(self):
        """Initialize the Document Service."""
        self.settings = document_service_settings
        self.minio_client = get_minio_client()
        self.prisma_client = get_prisma_client()
        self.error_handler = get_error_handler()
        self.metrics = get_metrics_collector()
        
    def _generate_document_path(self, user_id: str, category: str, filename: str) -> str:
        """
        Generate hierarchical storage path for document.
        
        Args:
            user_id: User identifier
            category: Document category
            filename: Original filename
            
        Returns:
            str: Storage path in format documents/{user_id}/{category}/{date}/{filename}
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"documents/{user_id}/{category}/{date_str}/{filename}"
    
    def _validate_document_metadata(self, metadata) -> None:
        """
        Validate document metadata against service rules.
        
        Args:
            metadata: DocumentMetadata from upload request
            
        Raises:
            ServiceValidationError: If validation fails
        """
        # Validate required fields using utility functions
        validate_user_id(metadata.user_id)
        validate_filename(metadata.filename)
        
        if not metadata.mime_type:
            raise ServiceValidationError("mime_type", "MIME type is required")
        
        if metadata.size <= 0:
            raise ServiceValidationError("size", "File size must be greater than 0", str(metadata.size))
        
        # Validate file size
        if metadata.size > self.settings.max_file_size:
            raise ServiceValidationError(
                "size", 
                f"File size exceeds maximum allowed size of {self.settings.max_file_size} bytes",
                str(metadata.size)
            )
        
        # Validate MIME type
        if not self.settings.is_allowed_mime_type(metadata.mime_type):
            raise ServiceValidationError(
                "mime_type",
                f"MIME type not allowed. Allowed types: {', '.join(self.settings.allowed_mime_types)}",
                metadata.mime_type
            )
        
        # Validate file extension
        if not self.settings.is_allowed_file_extension(metadata.filename):
            raise ServiceValidationError(
                "filename",
                f"File extension not allowed. Allowed extensions: {', '.join(self.settings.storage_allowed_extensions)}",
                metadata.filename
            )
    
    async def _check_user_quota(self, user_id: str, additional_bytes: int) -> None:
        """
        Check if user has sufficient quota for additional storage.
        
        Args:
            user_id: User identifier
            additional_bytes: Additional bytes to be stored
            
        Raises:
            QuotaExceededError: If quota would be exceeded
        """
        try:
            # Get current usage
            usage = await self.prisma_client.userusage.find_unique(
                where={"userId": user_id}
            )
            
            current_bytes = usage.totalBytes if usage else 0
            new_total = current_bytes + additional_bytes
            
            if new_total > self.settings.default_user_quota:
                raise QuotaExceededError(new_total, self.settings.default_user_quota)
                
        except PrismaError as e:
            logger.error(f"Database error checking quota for user {user_id}: {e}")
            raise DatabaseUnavailableError("check_quota", str(e))
    
    async def _update_user_usage(self, user_id: str, file_count_delta: int, bytes_delta: int) -> None:
        """
        Update user usage statistics.
        
        Args:
            user_id: User identifier
            file_count_delta: Change in file count (can be negative)
            bytes_delta: Change in bytes used (can be negative)
        """
        try:
            # Use upsert to handle both new and existing users
            await self.prisma_client.userusage.upsert(
                where={"userId": user_id},
                data={
                    "create": {
                        "userId": user_id,
                        "fileCount": max(0, file_count_delta),
                        "totalBytes": max(0, bytes_delta),
                        "updatedAt": datetime.now()
                    },
                    "update": {
                        "fileCount": {"increment": file_count_delta},
                        "totalBytes": {"increment": bytes_delta},
                        "updatedAt": datetime.now()
                    }
                }
            )
        except PrismaError as e:
            logger.error(f"Failed to update usage for user {user_id}: {e}")
            raise DatabaseUnavailableError("update_usage", str(e))

    async def UploadDocument(
        self, 
        request_iterator: AsyncIterator[UploadDocumentRequest], 
        context: grpc.aio.ServicerContext
    ) -> UploadDocumentResponse:
        """
        Upload a document with streaming support.
        
        Args:
            request_iterator: Stream of upload requests (metadata + chunks)
            context: gRPC context
            
        Returns:
            UploadDocumentResponse: Upload result with document ID and path
        """
        try:
            # First request should contain metadata
            first_request = await request_iterator.__anext__()
            
            if not first_request.HasField("metadata"):
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "First request must contain document metadata"
                )
            
            metadata = first_request.metadata
            
            # Validate metadata
            self._validate_document_metadata(metadata)
            
            # Check user quota
            await self._check_user_quota(metadata.user_id, metadata.size)
            
            # Generate document ID and storage path
            document_id = str(uuid.uuid4())
            storage_path = self._generate_document_path(
                metadata.user_id, 
                metadata.category, 
                metadata.filename
            )
            
            # Collect file chunks
            file_data = bytearray()
            async for request in request_iterator:
                if request.HasField("chunk"):
                    file_data.extend(request.chunk)
            
            # Verify file size matches metadata
            if len(file_data) != metadata.size:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    f"File size mismatch: expected {metadata.size}, got {len(file_data)}"
                )
            
            # Upload to MinIO with error handling
            try:
                def upload_operation():
                    return self.minio_client.client.put_object(
                        bucket_name=self.settings.minio_bucket,
                        object_name=storage_path,
                        data=file_data,
                        length=len(file_data),
                        content_type=metadata.mime_type
                    )
                
                await self.error_handler.handle_minio_operation("upload", upload_operation)
                logger.info(f"Uploaded file to MinIO: {storage_path}")
            except MinIOUnavailableError as e:
                record_minio_unavailable()
                await context.abort(e.code, e.message)
            
            # Save metadata to database with error handling
            try:
                async def create_document_operation():
                    return await self.prisma_client.document.create(
                        data={
                            "id": document_id,
                            "status": "COMPLETED",
                            "userId": metadata.user_id,
                            "category": metadata.category,
                            "filename": metadata.filename,
                            "path": storage_path,
                            "size": metadata.size,
                            "mimeType": metadata.mime_type,
                            "createdAt": datetime.now(),
                            "updatedAt": datetime.now()
                        }
                    )
                
                document = await self.error_handler.handle_database_operation(
                    "create_document", create_document_operation
                )
                
                # Update user usage statistics
                await self._update_user_usage(metadata.user_id, 1, metadata.size)
                
                # Record successful upload metrics
                record_upload_success(metadata.user_id, metadata.size)
                
                logger.info(f"Document {document_id} uploaded successfully for user {metadata.user_id}")
                
                return UploadDocumentResponse(
                    document_id=document_id,
                    path=storage_path,
                    size=metadata.size,
                    status="COMPLETED",
                    message="Document uploaded successfully"
                )
                
            except DatabaseUnavailableError as e:
                record_database_unavailable()
                # Cleanup MinIO object if database save fails
                try:
                    def cleanup_operation():
                        return self.minio_client.client.remove_object(
                            bucket_name=self.settings.minio_bucket,
                            object_name=storage_path
                        )
                    
                    await self.error_handler.handle_minio_operation("cleanup", cleanup_operation)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup MinIO object after DB error: {cleanup_error}")
                
                await context.abort(e.code, e.message)
                
        except QuotaExceededError as e:
            record_quota_exceeded()
            await context.abort(e.code, e.message)
        except DocumentServiceError as e:
            record_operation_failure()
            await context.abort(e.code, e.message)
        except Exception as e:
            record_operation_failure()
            logger.error(f"Unexpected error in UploadDocument: {e}")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                "Internal server error during upload"
            )

    async def DownloadDocument(
        self, 
        request: DownloadDocumentRequest, 
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator[DownloadDocumentResponse]:
        """
        Download a document with streaming support.
        
        Args:
            request: Download request with user_id and document_id
            context: gRPC context
            
        Yields:
            DownloadDocumentResponse: Document info followed by data chunks
        """
        try:
            # Get document metadata from database
            document = await self.prisma_client.document.find_unique(
                where={"id": request.document_id}
            )
            
            if not document:
                await context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    f"Document {request.document_id} not found"
                )
            
            # Verify user ownership
            if document.userId != request.user_id:
                await context.abort(
                    grpc.StatusCode.PERMISSION_DENIED,
                    "Access denied: document belongs to different user"
                )
            
            # Send document info first
            doc_info = DocumentInfo(
                document_id=document.id,
                filename=document.filename,
                mime_type=document.mimeType,
                size=document.size,
                created_at=document.createdAt.isoformat()
            )
            
            yield DownloadDocumentResponse(info=doc_info)
            
            # Stream file data from MinIO
            try:
                response = self.minio_client.client.get_object(
                    bucket_name=self.settings.minio_bucket,
                    object_name=document.path
                )
                
                # Stream in chunks
                chunk_size = 64 * 1024  # 64KB chunks
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    yield DownloadDocumentResponse(chunk=chunk)
                
                response.close()
                response.release_conn()
                
                # Record successful download
                record_download_success()
                
                logger.info(f"Document {request.document_id} downloaded by user {request.user_id}")
                
            except Exception as e:
                logger.error(f"MinIO download failed for {document.path}: {e}")
                await context.abort(
                    grpc.StatusCode.INTERNAL,
                    "Failed to download file from storage"
                )
                
        except DocumentServiceError as e:
            await context.abort(e.code, e.message)
        except Exception as e:
            logger.error(f"Unexpected error in DownloadDocument: {e}")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                "Internal server error during download"
            )

    async def DeleteDocument(
        self, 
        request: DeleteDocumentRequest, 
        context: grpc.aio.ServicerContext
    ) -> DeleteDocumentResponse:
        """
        Delete a document and update usage statistics.
        
        Args:
            request: Delete request with user_id and document_id
            context: gRPC context
            
        Returns:
            DeleteDocumentResponse: Deletion result with updated usage stats
        """
        try:
            # Get document metadata from database
            document = await self.prisma_client.document.find_unique(
                where={"id": request.document_id}
            )
            
            if not document:
                await context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    f"Document {request.document_id} not found"
                )
            
            # Verify user ownership
            if document.userId != request.user_id:
                await context.abort(
                    grpc.StatusCode.PERMISSION_DENIED,
                    "Access denied: document belongs to different user"
                )
            
            # Delete from MinIO
            try:
                self.minio_client.client.remove_object(
                    bucket_name=self.settings.minio_bucket,
                    object_name=document.path
                )
                logger.info(f"Deleted file from MinIO: {document.path}")
            except Exception as e:
                logger.error(f"MinIO deletion failed for {document.path}: {e}")
                # Continue with database deletion even if MinIO fails
            
            # Delete from database
            try:
                await self.prisma_client.document.delete(
                    where={"id": request.document_id}
                )
                
                # Update user usage statistics
                await self._update_user_usage(request.user_id, -1, -document.size)
                
                # Get updated usage stats
                usage = await self.prisma_client.userusage.find_unique(
                    where={"userId": request.user_id}
                )
                
                updated_usage = UsageStats(
                    user_id=request.user_id,
                    file_count=usage.fileCount if usage else 0,
                    total_bytes=usage.totalBytes if usage else 0,
                    last_updated=usage.updatedAt.isoformat() if usage else datetime.now().isoformat()
                )
                
                # Record successful deletion
                record_delete_success(request.user_id, document.size)
                
                logger.info(f"Document {request.document_id} deleted successfully for user {request.user_id}")
                
                return DeleteDocumentResponse(
                    success=True,
                    message="Document deleted successfully",
                    updated_usage=updated_usage
                )
                
            except PrismaError as e:
                logger.error(f"Database error deleting document: {e}")
                await context.abort(
                    grpc.StatusCode.INTERNAL,
                    "Failed to delete document from database"
                )
                
        except DocumentServiceError as e:
            await context.abort(e.code, e.message)
        except Exception as e:
            logger.error(f"Unexpected error in DeleteDocument: {e}")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                "Internal server error during deletion"
            )

    async def ListDocuments(
        self, 
        request: ListDocumentsRequest, 
        context: grpc.aio.ServicerContext
    ) -> ListDocumentsResponse:
        """
        List documents with filtering and pagination.
        
        Args:
            request: List request with user_id and optional filters
            context: gRPC context
            
        Returns:
            ListDocumentsResponse: List of documents with pagination info
        """
        try:
            # Build query filters
            where_clause = {"userId": request.user_id}
            
            if request.category:
                where_clause["category"] = request.category
            
            if request.date_filter:
                # Parse date filter (expecting YYYY-MM-DD format)
                try:
                    filter_date = datetime.strptime(request.date_filter, "%Y-%m-%d")
                    next_day = filter_date + timedelta(days=1)
                    where_clause["createdAt"] = {
                        "gte": filter_date,
                        "lt": next_day
                    }
                except ValueError:
                    await context.abort(
                        grpc.StatusCode.INVALID_ARGUMENT,
                        "Invalid date filter format. Use YYYY-MM-DD"
                    )
            
            # Handle pagination
            page_size = min(request.page_size or 50, 100)  # Max 100 items per page
            skip = 0
            
            if request.page_token:
                try:
                    skip = int(request.page_token)
                except ValueError:
                    await context.abort(
                        grpc.StatusCode.INVALID_ARGUMENT,
                        "Invalid page token"
                    )
            
            # Query documents
            documents = await self.prisma_client.document.find_many(
                where=where_clause,
                order={"createdAt": "desc"},
                skip=skip,
                take=page_size + 1  # Get one extra to check if there are more pages
            )
            
            # Check if there are more pages
            has_more = len(documents) > page_size
            if has_more:
                documents = documents[:-1]  # Remove the extra document
            
            # Convert to response format
            document_summaries = []
            for doc in documents:
                summary = DocumentSummary(
                    document_id=doc.id,
                    filename=doc.filename,
                    category=doc.category,
                    size=doc.size,
                    mime_type=doc.mimeType,
                    created_at=doc.createdAt.isoformat(),
                    updated_at=doc.updatedAt.isoformat(),
                    status=doc.status
                )
                document_summaries.append(summary)
            
            # Generate next page token
            next_page_token = ""
            if has_more:
                next_page_token = str(skip + page_size)
            
            # Get total count for the user (without pagination)
            total_count = await self.prisma_client.document.count(
                where={"userId": request.user_id}
            )
            
            logger.info(f"Listed {len(document_summaries)} documents for user {request.user_id}")
            
            return ListDocumentsResponse(
                documents=document_summaries,
                next_page_token=next_page_token,
                total_count=total_count
            )
            
        except PrismaError as e:
            logger.error(f"Database error listing documents: {e}")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                "Failed to list documents"
            )
        except Exception as e:
            logger.error(f"Unexpected error in ListDocuments: {e}")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                "Internal server error during listing"
            )

    async def GetDocumentUrl(
        self, 
        request: GetDocumentUrlRequest, 
        context: grpc.aio.ServicerContext
    ) -> GetDocumentUrlResponse:
        """
        Generate presigned URL for document access.
        
        Args:
            request: URL request with user_id, document_id, and optional expiry
            context: gRPC context
            
        Returns:
            GetDocumentUrlResponse: Presigned URL with expiry and document info
        """
        try:
            # Get document metadata from database
            document = await self.prisma_client.document.find_unique(
                where={"id": request.document_id}
            )
            
            if not document:
                await context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    f"Document {request.document_id} not found"
                )
            
            # Verify user ownership
            if document.userId != request.user_id:
                await context.abort(
                    grpc.StatusCode.PERMISSION_DENIED,
                    "Access denied: document belongs to different user"
                )
            
            # Generate presigned URL
            expiry_minutes = request.expiry_minutes or 30  # Default 30 minutes
            expires_delta = timedelta(minutes=expiry_minutes)
            
            try:
                presigned_url = self.minio_client.get_presigned_url(
                    bucket_name=self.settings.minio_bucket,
                    object_name=document.path,
                    expires=expires_delta
                )
                
                expires_at = datetime.now() + expires_delta
                
                # Create document summary
                doc_summary = DocumentSummary(
                    document_id=document.id,
                    filename=document.filename,
                    category=document.category,
                    size=document.size,
                    mime_type=document.mimeType,
                    created_at=document.createdAt.isoformat(),
                    updated_at=document.updatedAt.isoformat(),
                    status=document.status
                )
                
                logger.info(f"Generated presigned URL for document {request.document_id}")
                
                return GetDocumentUrlResponse(
                    presigned_url=presigned_url,
                    expires_at=expires_at.isoformat(),
                    document_info=doc_summary
                )
                
            except MinIOClientError as e:
                logger.error(f"Failed to generate presigned URL: {e}")
                await context.abort(
                    grpc.StatusCode.INTERNAL,
                    "Failed to generate document URL"
                )
                
        except PrismaError as e:
            logger.error(f"Database error getting document URL: {e}")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                "Failed to retrieve document information"
            )
        except Exception as e:
            logger.error(f"Unexpected error in GetDocumentUrl: {e}")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                "Internal server error during URL generation"
            )

    async def GetUsageStats(
        self, 
        request: GetUsageStatsRequest, 
        context: grpc.aio.ServicerContext
    ) -> GetUsageStatsResponse:
        """
        Get user storage usage statistics.
        
        Args:
            request: Usage stats request with user_id
            context: gRPC context
            
        Returns:
            GetUsageStatsResponse: Usage statistics and quota information
        """
        try:
            # Get user usage from database
            usage = await self.prisma_client.userusage.find_unique(
                where={"userId": request.user_id}
            )
            
            # Default values for new users
            file_count = usage.fileCount if usage else 0
            total_bytes = usage.totalBytes if usage else 0
            last_updated = usage.updatedAt.isoformat() if usage else datetime.now().isoformat()
            
            # Calculate quota information
            quota_limit = self.settings.default_user_quota
            quota_used = total_bytes
            quota_remaining = max(0, quota_limit - quota_used)
            quota_percentage = (quota_used / quota_limit * 100) if quota_limit > 0 else 0
            
            usage_stats = UsageStats(
                user_id=request.user_id,
                file_count=file_count,
                total_bytes=total_bytes,
                last_updated=last_updated
            )
            
            quota_info = QuotaInfo(
                quota_limit=quota_limit,
                quota_used=quota_used,
                quota_remaining=quota_remaining,
                quota_percentage=quota_percentage
            )
            
            logger.info(f"Retrieved usage stats for user {request.user_id}: {file_count} files, {total_bytes} bytes")
            
            return GetUsageStatsResponse(
                usage=usage_stats,
                quota=quota_info
            )
            
        except PrismaError as e:
            logger.error(f"Database error getting usage stats: {e}")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                "Failed to retrieve usage statistics"
            )
        except Exception as e:
            logger.error(f"Unexpected error in GetUsageStats: {e}")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                "Internal server error during stats retrieval"
            )


# Service factory function for dependency injection
def create_document_service() -> DocumentService:
    """
    Create and return a DocumentService instance.
    
    Returns:
        DocumentService: Configured document service instance
    """
    return DocumentService()