# MinIO Setup and Configuration

This document describes the MinIO infrastructure setup for the LumenSlate document storage service.

## Overview

MinIO is configured as a self-hosted object storage service that provides S3-compatible APIs for document storage. The service runs in Docker Compose alongside the main application.

## Configuration

### Environment Variables

The following environment variables configure MinIO:

```bash
# MinIO Server Configuration
MINIO_ROOT_USER=minioadmin          # MinIO admin username
MINIO_ROOT_PASSWORD=minioadmin      # MinIO admin password
MINIO_ENDPOINT=localhost:9000       # MinIO API endpoint
MINIO_SECURE=false                  # Use HTTPS (true/false)
MINIO_REGION=us-east-1             # MinIO region
MINIO_BUCKET=documents             # Default bucket name

# Document Service Configuration
STORAGE_BACKEND=minio              # Storage backend type
STORAGE_MAX_FILE_SIZE=50MB         # Maximum file size
DEFAULT_USER_QUOTA=1073741824      # Default user quota (1GB)
METRICS_PORT=9100                  # Metrics endpoint port
```

### Docker Compose Services

#### MinIO Service
- **API Port**: 9000 (S3-compatible API)
- **Console Port**: 9001 (Web management interface)
- **Health Check**: `/minio/health/live` endpoint
- **Data Persistence**: `minio_data` Docker volume

#### Application Integration
- **Dependency**: Application waits for MinIO health check
- **Network**: Shared `lumenslate-network`
- **Environment**: MinIO configuration passed to application

## Usage

### Starting Services

```bash
# Start all services (MinIO + Application)
docker-compose up -d

# Start only MinIO
docker-compose up -d minio

# View logs
docker-compose logs minio
docker-compose logs ai-microservice
```

### Accessing MinIO Console

1. **URL**: http://localhost:9001
2. **Username**: `minioadmin` (or value of `MINIO_ROOT_USER`)
3. **Password**: `minioadmin` (or value of `MINIO_ROOT_PASSWORD`)

### Verifying Setup

Use the built-in verification script:

```bash
# Run MinIO setup verification
python app/utils/minio_init.py

# Test MinIO client import
python -c "from app.utils.minio_client import get_minio_client; print('OK')"
```

### Health Checks

#### MinIO Server Health
```bash
curl -f http://localhost:9000/minio/health/live
```

#### Application Health (includes MinIO connectivity)
```bash
curl -f http://localhost:50051/health  # When health endpoint is implemented
```

## Bucket Structure

The service automatically creates the following buckets:

- **`documents`**: Primary storage for user documents
  - Path structure: `documents/{user_id}/{category}/{date}/{filename}`
- **`temp`**: Temporary files during upload processing
- **`backups`**: Document metadata backups

## Client Configuration

The MinIO client is configured in `app/utils/minio_client.py` with:

- **Connection pooling**: Automatic connection management
- **Retry logic**: Exponential backoff for failed operations
- **Health monitoring**: Comprehensive health checks
- **Bucket management**: Automatic bucket creation and verification

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure MinIO container is running: `docker-compose ps minio`
   - Check MinIO logs: `docker-compose logs minio`
   - Verify network connectivity: `docker network ls`

2. **Authentication Errors**
   - Verify `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` environment variables
   - Check that application uses correct credentials

3. **Bucket Access Issues**
   - Run verification script: `python app/utils/minio_init.py`
   - Check bucket permissions in MinIO console
   - Verify bucket names match configuration

4. **Health Check Failures**
   - Check MinIO container health: `docker-compose ps`
   - Verify health check endpoint: `curl http://localhost:9000/minio/health/live`
   - Review container resource limits

### Logs and Monitoring

```bash
# View MinIO server logs
docker-compose logs -f minio

# View application logs (MinIO client operations)
docker-compose logs -f ai-microservice

# Check container status
docker-compose ps

# View resource usage
docker stats lumenslate-minio
```

## Security Considerations

### Development Environment
- Default credentials (`minioadmin:minioadmin`) are acceptable
- HTTP connections are acceptable for local development
- No additional security configuration required

### Production Environment
- **Change default credentials**: Set strong `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD`
- **Enable HTTPS**: Set `MINIO_SECURE=true` and configure TLS certificates
- **Network security**: Use private networks and firewall rules
- **Access policies**: Configure bucket policies and IAM users as needed

## Performance Tuning

### Resource Allocation
```yaml
# docker-compose.yml - MinIO service resources
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Storage Configuration
- **SSD/NVMe**: Recommended for better I/O performance
- **Volume mounting**: Consider host path mounts for production
- **Backup strategy**: Regular data backups for production use

## API Compatibility

MinIO provides full S3 API compatibility, supporting:
- **Standard operations**: PUT, GET, DELETE, LIST
- **Multipart uploads**: For large files
- **Presigned URLs**: Temporary access URLs
- **Versioning**: Object version management
- **Encryption**: Server-side encryption support

For detailed API documentation, see: https://docs.min.io/