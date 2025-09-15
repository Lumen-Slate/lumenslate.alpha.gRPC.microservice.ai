# MinIO Storage Integration Requirements

## Executive Summary

This document outlines the requirements for integrating MinIO as an object storage service into the Lumen Slate AI microservice. MinIO will serve as the primary blob storage solution for storing proto files, gRPC service definitions, model artifacts, logs, and other binary data that needs to be persisted and accessed efficiently.

## Current Architecture Overview

### Existing Storage Solutions
- **Database Storage**: PostgreSQL (primary), TiDB (RAG), SQLite (local)
- **File System**: Local volume mounts (`./app/data:/app/data`)
- **External Services**: MongoDB, Google Cloud Storage (via Vertex AI)
- **Current Limitations**: No dedicated blob storage, limited scalability, no CDN capabilities

### Components Requiring Storage
- **Proto Files**: `ai_service.proto`, generated Python files (`_pb2.py`, `_pb2_grpc.py`)
- **gRPC Services**: Service definitions and generated code
- **Model Artifacts**: AI model files, embeddings, training data
- **Logs**: Application logs, audit trails, performance metrics
- **Configuration Files**: Dynamic configuration, feature flags
- **User Data**: Uploaded documents, processed files, temporary data
- **Backup Data**: Database backups, configuration snapshots

## MinIO Infrastructure Requirements

### 1. MinIO Server Setup

#### 1.1 Deployment Options
- **Standalone Mode**: Single MinIO server for development/testing
- **Distributed Mode**: Multi-node MinIO cluster for production
- **Docker Deployment**: Containerized setup via Docker Compose
- **Kubernetes**: Helm chart deployment for cloud environments

#### 1.2 Hardware Requirements
- **Development**: 4GB RAM, 2 CPU cores, 100GB storage
- **Production**: 16GB+ RAM, 4+ CPU cores, 1TB+ storage (scalable)
- **Storage**: SSD/NVMe recommended for performance
- **Network**: 1Gbps+ network interface for high throughput

#### 1.3 MinIO Version
- **Version**: MinIO >= RELEASE.2024-01-01T00-00-00Z
- **Features Required**: S3 API compatibility, versioning, encryption, lifecycle management

### 2. Docker Compose Integration

#### 2.1 MinIO Service Configuration
```yaml
services:
  minio:
    image: minio/minio:latest
    container_name: lumenslate-minio
    ports:
      - "9000:9000"        # MinIO API
      - "9001:9001"        # MinIO Console
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
      MINIO_REGION: ${MINIO_REGION:-us-east-1}
    volumes:
      - minio_data:/data
      - ./config/minio:/root/.minio
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - lumenslate-network

volumes:
  minio_data:
    driver: local
```

#### 2.2 MinIO Console Service (Optional)
```yaml
  minio-console:
    image: minio/console:latest
    container_name: lumenslate-minio-console
    ports:
      - "9090:9090"
    environment:
      MINIO_SERVER_URL: http://minio:9000
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    depends_on:
      - minio
    networks:
      - lumenslate-network
```

## Storage Organization and Buckets

### 3. Bucket Structure

#### 3.1 Primary Buckets
- **`proto-files`**: Protocol buffer definitions and generated code
- **`grpc-services`**: gRPC service implementations and stubs
- **`model-artifacts`**: AI models, embeddings, training data
- **`logs`**: Application logs, audit trails, metrics
- **`user-data`**: User-uploaded files, processed documents
- **`backups`**: Database backups, configuration snapshots
- **`temp`**: Temporary files, cache data
- **`config`**: Dynamic configuration files, feature flags

#### 3.2 Bucket Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": "*"},
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": ["arn:aws:s3:::proto-files/*"]
    }
  ]
}
```

#### 3.3 Object Naming Convention
- **Proto Files**: `proto-files/{service}/{version}/{filename}.proto`
- **Generated Code**: `proto-files/{service}/{version}/generated/{filename}_pb2.py`
- **Models**: `model-artifacts/{model_type}/{version}/{model_name}.{ext}`
- **Logs**: `logs/{service}/{date}/{hour}/{filename}.log`
- **User Data**: `user-data/{user_id}/{upload_id}/{filename}`

## Application Integration Requirements

### 4. Python Client Integration

#### 4.1 Dependencies
```txt
# requirements.txt additions
minio>=7.1.0
boto3>=1.28.0
botocore>=1.31.0
python-multipart>=0.0.6  # For file uploads
```

#### 4.2 MinIO Client Configuration
```python
# app/config/minio_config.py
from minio import Minio
from minio.error import S3Error
import os

class MinIOClient:
    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
            region=os.getenv("MINIO_REGION", "us-east-1")
        )
        self.buckets = {
            "proto_files": "proto-files",
            "grpc_services": "grpc-services",
            "model_artifacts": "model-artifacts",
            "logs": "logs",
            "user_data": "user-data",
            "backups": "backups",
            "temp": "temp",
            "config": "config"
        }
```

### 5. Storage Service Layer

#### 5.1 Core Storage Operations
```python
# app/services/storage_service.py
class StorageService:
    def __init__(self, minio_client: MinIOClient):
        self.minio = minio_client

    async def upload_file(self, bucket: str, object_name: str, file_path: str, metadata: dict = None) -> dict:
        """Upload file to MinIO bucket"""

    async def download_file(self, bucket: str, object_name: str, file_path: str) -> dict:
        """Download file from MinIO bucket"""

    async def delete_file(self, bucket: str, object_name: str) -> dict:
        """Delete file from MinIO bucket"""

    async def list_files(self, bucket: str, prefix: str = "", recursive: bool = False) -> list:
        """List files in MinIO bucket"""

    async def get_file_url(self, bucket: str, object_name: str, expires: int = 3600) -> str:
        """Generate presigned URL for file access"""

    async def copy_file(self, source_bucket: str, source_object: str,
                       dest_bucket: str, dest_object: str) -> dict:
        """Copy file between buckets or within bucket"""
```

#### 5.2 Specialized Services

##### 5.2.1 Proto File Storage Service
```python
# app/services/proto_storage_service.py
class ProtoStorageService(StorageService):
    async def upload_proto_file(self, service_name: str, version: str,
                               proto_content: str, filename: str) -> dict:
        """Upload proto file with versioning"""

    async def upload_generated_code(self, service_name: str, version: str,
                                   code_content: str, filename: str) -> dict:
        """Upload generated Python code"""

    async def get_proto_versions(self, service_name: str) -> list:
        """Get available versions for a service"""

    async def download_proto_file(self, service_name: str, version: str, filename: str) -> str:
        """Download proto file content"""
```

##### 5.2.2 Model Artifact Storage Service
```python
# app/services/model_storage_service.py
class ModelStorageService(StorageService):
    async def upload_model(self, model_type: str, version: str,
                          model_path: str, metadata: dict) -> dict:
        """Upload AI model with metadata"""

    async def download_model(self, model_type: str, version: str) -> str:
        """Download model to local path"""

    async def list_models(self, model_type: str = None) -> list:
        """List available models"""

    async def delete_model_version(self, model_type: str, version: str) -> dict:
        """Delete specific model version"""
```

##### 5.2.3 Log Storage Service
```python
# app/services/log_storage_service.py
class LogStorageService(StorageService):
    async def upload_log_file(self, service_name: str, log_content: str,
                             date: str, hour: str) -> dict:
        """Upload log file with timestamp"""

    async def get_logs_by_date(self, service_name: str, date: str) -> list:
        """Retrieve logs for specific date"""

    async def rotate_logs(self, service_name: str, retention_days: int = 30) -> dict:
        """Rotate old log files"""
```

### 6. gRPC Service Integration

#### 6.1 New gRPC Services
```protobuf
// storage_service.proto
service StorageService {
  rpc UploadFile(UploadFileRequest) returns (UploadFileResponse);
  rpc DownloadFile(DownloadFileRequest) returns (DownloadFileResponse);
  rpc DeleteFile(DeleteFileRequest) returns (DeleteFileResponse);
  rpc ListFiles(ListFilesRequest) returns (ListFilesResponse);
  rpc GetFileUrl(GetFileUrlRequest) returns (GetFileUrlResponse);
}

service ProtoStorageService {
  rpc UploadProtoFile(UploadProtoRequest) returns (UploadProtoResponse);
  rpc GetProtoVersions(GetProtoVersionsRequest) returns (GetProtoVersionsResponse);
  rpc DownloadProtoFile(DownloadProtoRequest) returns (DownloadProtoResponse);
}
```

#### 6.2 Service Implementation
```python
# app/services/grpc_storage_services.py
class StorageGRPCService(storage_pb2_grpc.StorageServiceServicer):
    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service

    async def UploadFile(self, request, context):
        try:
            result = await self.storage_service.upload_file(
                bucket=request.bucket,
                object_name=request.object_name,
                file_path=request.file_path,
                metadata=dict(request.metadata)
            )
            return storage_pb2.UploadFileResponse(
                success=True,
                message="File uploaded successfully",
                object_name=result["object_name"],
                bucket=result["bucket"],
                size=result["size"],
                etag=result["etag"]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return storage_pb2.UploadFileResponse(success=False, message=str(e))
```

## Environment Configuration

### 7. Environment Variables

#### 7.1 MinIO Configuration
```bash
# MinIO Server Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=lumenslate_minio
MINIO_SECRET_KEY=lumenslate_minio_secret
MINIO_SECURE=false
MINIO_REGION=us-east-1

# MinIO Console (optional)
MINIO_CONSOLE_ENDPOINT=localhost:9090

# Storage Configuration
STORAGE_BACKEND=minio  # Options: minio, local, gcs, s3
STORAGE_DEFAULT_BUCKET=user-data
STORAGE_MAX_FILE_SIZE=100MB
STORAGE_ALLOWED_EXTENSIONS=pdf,doc,docx,txt,json,yaml,yml,pickle,pkl,h5

# Proto Storage Configuration
PROTO_STORAGE_BUCKET=proto-files
PROTO_STORAGE_VERSIONING=true
PROTO_GENERATED_CODE_BUCKET=grpc-services

# Model Storage Configuration
MODEL_STORAGE_BUCKET=model-artifacts
MODEL_STORAGE_COMPRESSION=true
MODEL_STORAGE_ENCRYPTION=true

# Log Storage Configuration
LOG_STORAGE_BUCKET=logs
LOG_STORAGE_RETENTION_DAYS=30
LOG_STORAGE_COMPRESSION=gzip
```

#### 7.2 Docker Environment
```yaml
# docker-compose.yml environment additions
environment:
  # ... existing environment variables ...
  MINIO_ENDPOINT: ${MINIO_ENDPOINT:-minio:9000}
  MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
  MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
  MINIO_SECURE: ${MINIO_SECURE:-false}
  STORAGE_BACKEND: ${STORAGE_BACKEND:-minio}
```

## Security Requirements

### 8. Authentication and Authorization

#### 8.1 MinIO Security
- **Access Keys**: Separate access keys for different services
- **Bucket Policies**: Granular permissions per bucket
- **TLS/SSL**: Enable HTTPS for production deployments
- **Audit Logging**: Enable MinIO audit logs

#### 8.2 Application Security
- **API Key Management**: Secure storage of MinIO credentials
- **Request Signing**: Use presigned URLs for secure access
- **Rate Limiting**: Implement rate limiting for storage operations
- **Input Validation**: Validate file types, sizes, and content

### 9. Monitoring and Observability

#### 9.1 MinIO Monitoring
- **Health Checks**: Container health checks
- **Metrics**: MinIO metrics endpoint integration
- **Alerts**: Storage usage, error rates, performance metrics
- **Logs**: Centralized logging for MinIO operations

#### 9.2 Application Monitoring
```python
# app/utils/storage_monitoring.py
class StorageMonitor:
    def __init__(self, minio_client: MinIOClient):
        self.minio = minio_client

    async def get_storage_stats(self) -> dict:
        """Get storage usage statistics"""

    async def monitor_bucket_usage(self, bucket: str) -> dict:
        """Monitor specific bucket usage"""

    async def alert_on_thresholds(self, thresholds: dict) -> None:
        """Alert when storage thresholds are exceeded"""
```

## Performance and Scalability

### 10. Performance Optimization

#### 10.1 Caching Strategy
- **Metadata Caching**: Cache frequently accessed file metadata
- **CDN Integration**: Use CDN for static file serving
- **Connection Pooling**: Reuse MinIO client connections

#### 10.2 Data Transfer Optimization
- **Multipart Upload**: For large files (>100MB)
- **Compression**: Enable compression for text-based files
- **Streaming**: Stream large files instead of loading in memory

#### 10.3 Database Integration
- **Metadata Storage**: Store file metadata in PostgreSQL/TiDB
- **Indexing**: Index file metadata for fast queries
- **Caching**: Cache frequently accessed metadata

## Migration Strategy

### 11. Implementation Phases

#### 11.1 Phase 1: Infrastructure Setup (Week 1)
- Deploy MinIO server via Docker Compose
- Configure buckets and policies
- Set up monitoring and logging
- Test basic connectivity

#### 11.2 Phase 2: Core Integration (Weeks 2-3)
- Implement MinIO client configuration
- Create storage service layer
- Add basic upload/download operations
- Integrate with existing gRPC services

#### 11.3 Phase 3: Specialized Services (Weeks 4-5)
- Implement proto file storage service
- Add model artifact storage
- Create log storage functionality
- Develop user data management

#### 11.4 Phase 4: Advanced Features (Week 6)
- Implement versioning and lifecycle management
- Add encryption and compression
- Set up backup and disaster recovery
- Performance optimization

#### 11.5 Phase 5: Migration and Testing (Weeks 7-8)
- Migrate existing data to MinIO
- Comprehensive testing and validation
- Performance benchmarking
- Production deployment

### 12. Testing Requirements

#### 12.1 Unit Tests
```python
# tests/test_storage_service.py
class TestStorageService:
    def test_upload_file(self):
        """Test file upload functionality"""

    def test_download_file(self):
        """Test file download functionality"""

    def test_delete_file(self):
        """Test file deletion functionality"""

    def test_list_files(self):
        """Test file listing functionality"""
```

#### 12.2 Integration Tests
- **End-to-End Testing**: Complete file upload/download workflows
- **Load Testing**: Performance testing under load
- **Failure Testing**: Network failures, MinIO outages
- **Security Testing**: Access control and authentication

### 13. Backup and Disaster Recovery

#### 13.1 Backup Strategy
- **Automated Backups**: Daily backups of critical buckets
- **Versioning**: Enable object versioning for recovery
- **Cross-Region Replication**: Replicate to multiple MinIO instances
- **Database Backups**: Backup metadata alongside files

#### 13.2 Recovery Procedures
- **Point-in-Time Recovery**: Restore to specific timestamps
- **Bucket Recovery**: Restore entire buckets from backups
- **Failover**: Automatic failover to backup MinIO instances

### 14. Cost Analysis

#### 14.1 Infrastructure Costs
- **Storage Costs**: $0.02-0.05/GB/month for object storage
- **Network Costs**: Data transfer and CDN costs
- **Compute Costs**: MinIO server compute resources

#### 14.2 Operational Costs
- **Monitoring**: Logging and monitoring infrastructure
- **Backup**: Backup storage and transfer costs
- **Maintenance**: Regular maintenance and updates

### 15. Success Criteria

#### 15.1 Functional Success
- All storage operations working correctly
- Seamless integration with existing services
- Performance meets or exceeds requirements
- Data integrity maintained throughout

#### 15.2 Performance Success
- File upload/download < 5 seconds for typical files
- Support for concurrent operations
- Minimal latency impact on existing services
- Scalable to handle growth

#### 15.3 Operational Success
- Comprehensive monitoring and alerting
- Automated backup and recovery procedures
- Clear documentation and runbooks
- Minimal downtime during deployment

## Appendices

### Appendix A: MinIO Configuration Files
### Appendix B: Bucket Policy Templates
### Appendix C: API Documentation
### Appendix D: Performance Benchmarks
### Appendix E: Troubleshooting Guide</content>
<parameter name="filePath">d:\lumenslate\lumenslate.alpha.fastapi.microservice.ai\MINIO_STORAGE_INTEGRATION_REQUIREMENTS.md
