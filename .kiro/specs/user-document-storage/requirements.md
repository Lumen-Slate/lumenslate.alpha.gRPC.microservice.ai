# Requirements Document

## Introduction

This document defines requirements for a **User Document Storage Service** that integrates with **MinIO** as the self-hosted object storage layer and **TiDB** accessed via **Prisma ORM** for metadata and usage tracking in the LumenSlate AI platform.

The service provides organized storage for user documents (PDF, DOCX, XLSX, TXT) with **gRPC APIs** for file operations, quota management, usage tracking, and a **JSON-based monitoring endpoint**. Authentication is not enforced in this version to simplify initial implementation.

This implementation involves migrating from the current **SQLAlchemy ORM** to **Prisma ORM** for improved type safety, better developer experience, and enhanced database management capabilities.

---

## Requirements

### Requirement 1: MinIO Deployment and Infrastructure

**User Story:** As a system administrator, I want MinIO to be deployed via Docker Compose with proper configuration, so that the document storage infrastructure is reliable and maintainable.

**Acceptance Criteria**

1. WHEN the system starts THEN MinIO SHALL run via Docker Compose with API on port `9000` and console on port `9001`.
2. WHEN MinIO initializes THEN the system SHALL create a `documents` bucket idempotently.
3. WHEN configuring MinIO THEN the system SHALL use environment variables for endpoint, access key, secret key, and region.
4. WHEN health checks are performed THEN they SHALL complete within 10 seconds.

---

### Requirement 2: Database Integration via Prisma ORM (TiDB) - Migration from SQLAlchemy

**User Story:** As a system administrator, I want to migrate from SQLAlchemy ORM to Prisma ORM to manage the TiDB schema and queries, so that metadata and usage statistics are consistent, maintainable, and benefit from improved type safety and developer experience.

**Acceptance Criteria**

1. WHEN the service starts THEN it SHALL connect to TiDB via the Prisma client using a DSN configured via environment variables (e.g., `MICROSERVICE_DATABASE`).
2. WHEN migrating from SQLAlchemy THEN the existing database schema SHALL be introspected and converted to Prisma schema format, maintaining data integrity.
3. WHEN schema changes are applied THEN Prisma migrations SHALL be applied via `prisma migrate deploy` (or equivalent) to update TiDB.
4. WHEN a document is uploaded THEN Prisma SHALL insert a new record into the `RagDocument` model with metadata:

   * `id` (UUID)
   * `status` (enum: "pending", "completed", "failed")
   * `userId`
   * `category`
   * `filename`
   * `path`
   * `size`
   * `mimeType`
   * `createdAt`
   * `updatedAt`
5. WHEN a document is deleted THEN Prisma SHALL remove or mark the corresponding `Document` record as deleted (soft-delete option configurable).
6. WHEN usage statistics are updated THEN Prisma SHALL maintain a `UserUsage` model that stores per-user totals (`fileCount`, `totalBytes`) and updated timestamps.
7. WHEN quotas are enforced THEN the service SHALL check `UserUsage` via Prisma before accepting new uploads.
8. WHEN TiDB is unavailable THEN the service SHALL return structured gRPC errors and increment `database_unavailable_total` metric.

> Implementation note (for developers): provide a `schema.prisma` with `Document` and `UserUsage` models, and ensure transactional updates (or retries) when updating both MinIO and TiDB state to avoid inconsistency. Plan the migration from SQLAlchemy models to Prisma schema carefully, ensuring all existing relationships and constraints are preserved.

---

### Requirement 3: Document Upload Operations

**User Story:** As a user, I want to upload documents to organized storage locations, so that my files are securely stored and easily retrievable.

**Acceptance Criteria**

1. WHEN a user uploads a document THEN the system SHALL store it in MinIO under:
   `documents/{user_id}/{category}/{date}/{filename}`.
2. WHEN uploading a document THEN the system SHALL validate the MIME type against configurable allowed types (default: PDF, DOCX, XLSX, TXT).
3. WHEN uploading a document THEN the system SHALL enforce a configurable maximum file size (default: 50 MB).
4. WHEN uploading large files THEN the system SHALL support streaming upload via gRPC.
5. WHEN a user uploads a document THEN Prisma SHALL persist metadata in `Document` and update `UserUsage`.
6. WHEN an upload fails validation THEN the system SHALL return a structured gRPC error.

---

### Requirement 4: Document Retrieval Operations

**User Story:** As a user, I want to download and access my stored documents, so that I can retrieve my files when needed.

**Acceptance Criteria**

1. WHEN a user requests document download THEN the system SHALL retrieve the file from MinIO or provide a presigned URL.
2. WHEN downloading large files THEN the system SHALL support streaming download via gRPC.
3. WHEN a user requests a presigned URL THEN the system SHALL return a URL with configurable expiry (default: 30 minutes).
4. WHEN a presigned URL expires THEN access SHALL be denied.
5. WHEN a user lists documents THEN the system SHALL fetch metadata from TiDB via Prisma and return name, size, createdAt, and category.

---

### Requirement 5: Document Management Operations

**User Story:** As a user, I want to delete my documents and view my storage usage, so that I can manage my storage quota effectively.

**Acceptance Criteria**

1. WHEN a user deletes a document THEN the system SHALL remove the file from MinIO and confirm deletion.
2. WHEN a document is deleted THEN Prisma SHALL update or remove the `Document` record and adjust the `UserUsage` totals.
3. WHEN a user requests usage statistics THEN the system SHALL return data from `UserUsage` (current storage size and file count).
4. WHEN a user exceeds their quota THEN upload operations SHALL be rejected with an appropriate error and `documents_quota_exceeded_total` SHALL be incremented.

---

### Requirement 6: Monitoring and Observability

**User Story:** As a system administrator, I want monitoring and logging of document operations, so that I can track system health and usage activity.

**Acceptance Criteria**

1. WHEN any document operation occurs THEN the system SHALL log the event with `userId`, `filename`, `size`, `operationType` (upload/download/delete), and `timestamp` in structured JSON.
2. WHEN metrics are collected THEN the service SHALL expose an HTTP endpoint `/metrics` on a configurable port (default: `9100`).
3. WHEN `/metrics` is requested THEN it SHALL return JSON including at least:

   * `documents_upload_total`
   * `documents_download_total`
   * `documents_delete_total`
   * `documents_storage_bytes` (per user and global)
   * `documents_errors_total`
   * `documents_quota_exceeded_total`
   * `minio_unavailable_total`
   * `database_unavailable_total`
   * `documents_operation_failures_total`
   * `last_updated` (ISO timestamp)
4. WHEN logs are generated THEN they SHALL be rotated daily and retained for 30 days (configurable).
5. WHEN a user exceeds quota THEN the system SHALL log an event and increment `documents_quota_exceeded_total`.
6. WHEN MinIO becomes unavailable THEN the system SHALL log the error and increment `minio_unavailable_total`.
7. WHEN TiDB becomes unavailable THEN the system SHALL log the error and increment `database_unavailable_total`.
8. WHEN repeated upload/download failures occur THEN the system SHALL increment `documents_operation_failures_total`.

---

### Requirement 7: gRPC Service Interface

**User Story:** As a client application developer, I want a well-defined gRPC service interface for document operations, so that I can integrate document storage functionality into applications.

**Acceptance Criteria**

1. WHEN the service starts THEN it SHALL expose a gRPC service called `DocumentService`.
2. WHEN the `DocumentService` is available THEN it SHALL provide the following methods:

   * `UploadDocument` (streaming upload)
   * `DownloadDocument` (streaming download)
   * `DeleteDocument`
   * `ListDocuments` (filter by userId, category, date)
   * `GetDocumentUrl` (presigned URL generation)
   * `GetUsageStats` (per-user usage)
3. WHEN gRPC methods are called THEN they SHALL follow Protocol Buffer message definitions and return structured error details on failure.
4. WHEN errors occur THEN the service SHALL return appropriate gRPC status codes and structured error messages.

---

## Implementation Notes & Developer Guidance (brief)

* **SQLAlchemy to Prisma Migration:** Plan the migration carefully by first introspecting the existing SQLAlchemy models and database schema. Use `prisma db pull` to generate an initial Prisma schema from the existing TiDB database, then refine the schema as needed. Ensure all existing relationships, indexes, and constraints are properly represented in the new Prisma schema.
* **Prisma + TiDB:** Use Prisma v4+ with the MySQL-compatible TiDB connector (`MICROSERVICE_DATABASE` pointing to the TiDB instance). Provide `schema.prisma` with `Document` and `UserUsage` models and use `prisma migrate` workflow for deployments.
* **Transactions & Consistency:** Implement safe ordering and/or compensating transactions: e.g., upload file to MinIO first, then create DB record; if DB write fails, delete object from MinIO or flag for cleanup. Prefer idempotent operations and retries.
* **Metrics Storage:** In-memory counters with periodic persistence/aggregation (if needed). Ensure metrics include per-user totals pulled from `UserUsage`.
* **No Authentication:** This version intentionally omits authentication. Keep `userId` in paths and DB to allow future addition of auth without schema changes.
* **Configuration:** All endpoints, credentials, timeouts, quotas, and allowed MIME types MUST be configurable via environment variables or a config file.
* **Health Checks:** Expose a health endpoint that checks MinIO and TiDB connectivity and returns status within 10s.
