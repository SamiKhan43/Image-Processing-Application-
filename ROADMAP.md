# 🗺️ Pictura — Project Roadmap

Pictura is an image-processing API built with FastAPI, SQLAlchemy, JWT authentication, and Pillow. This roadmap outlines its evolution from a locally running application into a secure, scalable, and cloud-ready image-processing service.

The development plan prioritizes completing core functionality, strengthening security, improving performance, and gradually introducing distributed infrastructure.

> **Status Key:** `[ ]` Planned | `[~]` In Progress | `[x]` Completed

---

## Development Overview

Pictura will evolve through four stages:

1. **Core Functionality** — Complete the API and improve its reliability.
2. **Security & Production Readiness** — Strengthen authentication, validation, testing, and data management.
3. **Cloud & Distributed Architecture** — Introduce cloud storage, background workers, and scalable infrastructure.
4. **Advanced Image Processing** — Add flexible processing pipelines and developer-oriented features.

---

##  Architecture Evolution

### Current Architecture

The initial implementation uses a straightforward architecture designed to establish the application's core functionality.

- **API Layer:** FastAPI routes handle authentication, image uploads, and processing requests.
- **Processing Engine:** Pillow performs image transformations.
- **Database:** SQLite stores user accounts and image metadata.
- **File Storage:** Original and transformed images are stored on the local filesystem.
- **Authentication:** JWT access tokens and password hashing protect user accounts.

### Target Architecture

The long-term goal is to build an architecture that can handle larger workloads and multiple application instances.

- **API Layer:** FastAPI with rate limiting, request validation, and structured logging.
- **Processing Engine:** Background workers execute computationally expensive transformations.
- **Database:** PostgreSQL with Alembic-managed schema migrations.
- **File Storage:** An abstraction layer supporting local storage and S3-compatible object storage.
- **Caching:** Redis reduces repeated work and improves response times where appropriate.
- **Task Queue:** Celery or another suitable task-processing system manages background jobs.
- **Observability:** Structured logs, request tracking, and application metrics.

### Technology Evolution

| Component | Current Implementation | Planned Evolution |
|---|---|---|
| API Framework | FastAPI | FastAPI with production middleware |
| Authentication | JWT access tokens | Access and rotating refresh tokens |
| Password Security | Argon2-based hashing | Maintain secure password hashing |
| Database | SQLite | PostgreSQL and Alembic |
| File Storage | Local filesystem | Pluggable local and S3-compatible storage |
| Image Processing | Pillow | Optimized processing pipelines |
| Background Jobs | In-request processing | Distributed task workers |
| Caching | Local application flow | Redis where beneficial |
| Testing | Initial development | Comprehensive automated tests |
| Logging | Standard application logs | Structured JSON logging |
| Deployment | Local development | Docker-based production deployment |

---

## Phase 1: Core Functionality & API Improvements

**Goal:** Complete the essential API features and establish reliable application behavior.

### Image Management

- [ ] **Image Listing and Pagination**
  - Add pagination to `GET /images`.
  - Support query parameters such as `page` and `limit`.
  - Add optional filtering by image format and upload date.
  - Return consistent pagination metadata.

- [ ] **Image Deletion**
  - Implement `DELETE /images/{image_id}`.
  - Remove the associated image metadata and stored files.
  - Ensure users can delete only their own images.
  - Handle missing files and database failures safely.

- [ ] **Image Metadata Retrieval**
  - Implement `GET /images/{image_id}`.
  - Return metadata such as the image format, dimensions, file size, and creation date.
  - Enforce ownership checks.

- [ ] **Transformed Image Retrieval**
  - Add an endpoint to retrieve or download transformed images.
  - Verify image ownership before providing access.
  - Handle missing or expired resources appropriately.

### API Reliability

- [ ] **Consistent Error Responses**
  - Standardize error response structures.
  - Use appropriate HTTP status codes.
  - Avoid exposing internal exceptions or sensitive implementation details.

- [ ] **Request Validation**
  - Validate image-processing parameters.
  - Reject invalid dimensions, crop coordinates, rotation values, and unsupported formats.
  - Set sensible limits on image dimensions and file sizes.

- [ ] **API Documentation**
  - Improve endpoint descriptions and request examples.
  - Document authentication requirements and error responses.
  - Keep the OpenAPI documentation accurate.

---

##  Phase 2: Security, Testing & Production Readiness

**Goal:** Make Pictura more secure, maintainable, and reliable.

### Authentication & Security

- [ ] **Refresh Token Authentication**
  - Introduce short-lived access tokens and refresh tokens.
  - Rotate refresh tokens when they are used.
  - Define a secure session expiration and revocation strategy.

- [ ] **Logout and Session Revocation**
  - Add a logout endpoint.
  - Invalidate refresh-token sessions.
  - Define how revoked tokens are handled.

- [ ] **Application Rate Limiting**
  - Protect login and other sensitive endpoints.
  - Apply stricter limits to expensive image-processing operations.
  - Introduce shared rate-limit storage if multiple application instances are deployed.

- [ ] **Secure File Access**
  - Enforce ownership checks on image operations.
  - Prevent path traversal and unauthorized file access.
  - Validate uploaded content instead of relying exclusively on filenames or MIME types.

### Automated Testing

- [ ] **Unit Tests**
  - Test individual image-processing functions.
  - Cover resizing, cropping, rotation, flipping, filtering, and format conversion.
  - Test invalid inputs and edge cases.

- [ ] **API Integration Tests**
  - Test authentication and protected routes.
  - Test image uploads, transformations, retrieval, and deletion.
  - Verify that users cannot access another user's images.

- [ ] **Test Database Isolation**
  - Use a separate test database.
  - Keep tests independent and repeatable.
  - Verify database relationships and deletion behavior.

- [ ] **Continuous Integration**
  - Run automated tests on every push and pull request.
  - Add linting and formatting checks with Ruff.
  - Introduce static type checking where useful.

### Application Observability

- [ ] **Structured Logging**
  - Replace unstructured diagnostic output with consistent application logs.
  - Include useful context without logging passwords, tokens, or other secrets.

- [ ] **Request ID Tracking**
  - Assign a request ID to each incoming request.
  - Include it in relevant logs and error responses.

- [ ] **Health Check Endpoints**
  - Add a basic application health endpoint.
  - Add readiness checks for required dependencies where appropriate.

---

##  Phase 3: Database & Storage Evolution

**Goal:** Remove local infrastructure limitations and prepare for deployment across multiple instances.

### Database Migration

- [ ] **Migrate to PostgreSQL**
  - Replace SQLite with PostgreSQL.
  - Update database configuration to use environment variables.
  - Verify models, relationships, constraints, and queries.

- [ ] **Database Schema Migrations**
  - Integrate Alembic.
  - Track database schema changes through versioned migrations.
  - Document the migration process for development and deployment.

### Storage Abstraction

- [ ] **Introduce a Storage Interface**
  - Separate storage operations from API routes and processing logic.
  - Define a consistent interface for uploading, retrieving, and deleting files.
  - Keep the local filesystem as a supported backend.

- [ ] **S3-Compatible Object Storage**
  - Add support for AWS S3 or another compatible provider.
  - Evaluate Cloudflare R2 and MinIO as alternatives.
  - Store object identifiers and metadata instead of relying on local paths.

- [ ] **Storage Configuration**
  - Configure storage through environment variables.
  - Keep credentials outside the source code.
  - Support separate development and production configurations.

- [ ] **Storage Consistency**
  - Handle failures between database operations and file deletion.
  - Define cleanup behavior for orphaned files.
  - Make upload and deletion operations resilient to partial failures.

---

##  Phase 4: Performance & Asynchronous Processing

**Goal:** Handle expensive image transformations without keeping API requests open unnecessarily.

### Background Processing

- [ ] **Background Task Queue**
  - Evaluate Celery with Redis or RabbitMQ.
  - Move expensive transformations into background workers.
  - Return `202 Accepted` when a processing request is accepted for asynchronous execution.

- [ ] **Processing Job Management**
  - Create a processing-job model.
  - Track states such as `pending`, `processing`, `completed`, and `failed`.
  - Store the result or error information associated with each job.

- [ ] **Job Status Endpoint**
  - Implement an endpoint such as `GET /jobs/{job_id}`.
  - Allow users to check processing progress and retrieve results.
  - Enforce job ownership.

- [ ] **Worker Reliability**
  - Handle task failures and retries.
  - Prevent duplicate processing where necessary.
  - Define timeouts and resource limits for expensive jobs.

### Caching & Optimization

- [ ] **Redis Caching**
  - Cache suitable metadata and frequently requested information.
  - Define cache expiration and invalidation rules.
  - Avoid caching private user data without appropriate isolation.

- [ ] **Duplicate Processing Detection**
  - Calculate image hashes where useful.
  - Identify repeated processing requests.
  - Reuse results only when the input and all relevant transformation parameters match.

- [ ] **Processing Performance**
  - Profile expensive operations before optimizing them.
  - Reduce unnecessary file reads and writes.
  - Evaluate memory usage when processing large images.

---

##  Phase 5: Advanced Image Processing

**Goal:** Expand Pictura's image-processing capabilities and make transformations more flexible.

### Processing Features

- [ ] **Batch Image Processing**
  - Allow multiple images to be submitted for processing.
  - Return individual results and errors for each image.
  - Apply limits to batch size and total processing resources.

- [ ] **Chained Transformations**
  - Allow multiple operations in one request.
  - Support ordered pipelines such as resize → crop → filter → format conversion.
  - Validate the complete pipeline before execution where possible.

- [ ] **Image Compression Controls**
  - Allow clients to configure output quality.
  - Support appropriate compression settings for JPEG and WebP.
  - Measure the trade-off between output size and visual quality.

- [ ] **Thumbnail Generation**
  - Generate thumbnails for uploaded images.
  - Support configurable dimensions.
  - Avoid unnecessary regeneration of unchanged thumbnails.

- [ ] **Additional Filters and Effects**
  - Expand the available image filters.
  - Support configurable filter intensity.
  - Validate parameters and keep processing behavior predictable.

- [ ] **Image Information Extraction**
  - Return image dimensions, format, color mode, and file size.
  - Define how EXIF metadata is handled.
  - Avoid unintentionally exposing sensitive metadata.

---

## Phase 6: Developer Experience & Integrations

**Goal:** Make Pictura easier to integrate into other applications.

### API Improvements

- [ ] **API Versioning**
  - Introduce versioned routes when compatibility requirements justify them.
  - Document breaking changes and migration paths.

- [ ] **API Keys**
  - Allow users to create and revoke API keys.
  - Store only securely hashed key values.
  - Support scopes, usage limits, and expiration where appropriate.

- [ ] **Usage Tracking**
  - Track processing requests and resource consumption.
  - Add per-user usage summaries.
  - Establish limits before introducing subscription-based features.

### Webhooks

- [ ] **Processing Event Notifications**
  - Notify clients when asynchronous processing completes or fails.
  - Include event identifiers and relevant job information.

- [ ] **Webhook Security**
  - Sign webhook payloads.
  - Define retry policies and delivery timeouts.
  - Provide a way to verify webhook authenticity.

---

##  Phase 7: Deployment & Distributed Architecture

**Goal:** Prepare Pictura for reliable deployment and horizontal scaling.

### Containerization

- [ ] **Production Docker Configuration**
  - Optimize the Docker image.
  - Run the application as a non-root user.
  - Separate development and production configurations.

- [ ] **Docker Compose Deployment**
  - Configure the API, database, and required supporting services.
  - Add persistent storage and health checks.
  - Document environment variables and startup procedures.

### Cloud Deployment

- [ ] **Cloud Deployment**
  - Deploy the API to a suitable hosting platform.
  - Configure production secrets and environment variables.
  - Set up HTTPS and appropriate network access controls.

- [ ] **Horizontal Scaling**
  - Run multiple API instances when needed.
  - Use shared database and object storage services.
  - Move shared rate-limit and cache state out of individual application processes.

- [ ] **Metrics and Monitoring**
  - Track request latency, error rates, and processing duration.
  - Monitor worker health and queue depth.
  - Evaluate OpenTelemetry when distributed tracing becomes useful.

- [ ] **Infrastructure Orchestration**
  - Evaluate Kubernetes when deployment complexity or scaling requirements justify it.
  - Add deployment manifests and Helm charts only when needed.

---

##  Recommended Implementation Order

The roadmap is intentionally progressive. Each phase builds on the foundations established by the previous phases.

1. **Complete the core API:** Image metadata, listing, retrieval, and deletion.
2. **Add automated tests:** Verify image processing, authentication, ownership, and error handling.
3. **Strengthen security:** Implement rate limiting, secure file access, and refresh-token management.
4. **Improve developer experience:** Add consistent errors, logging, request IDs, and health checks.
5. **Migrate the database:** Introduce PostgreSQL and Alembic.
6. **Abstract file storage:** Preserve local storage while adding an S3-compatible backend.
7. **Introduce asynchronous processing:** Add background jobs and job-status tracking.
8. **Optimize performance:** Measure bottlenecks before adding caching or deduplication.
9. **Expand image processing:** Add batch operations, chained transformations, and compression controls.
10. **Prepare for deployment:** Configure production Docker, cloud hosting, and monitoring.
11. **Add advanced integrations:** Introduce API keys, webhooks, and orchestration when the core service is stable.

---

##  Long-Term Vision

Pictura aims to become a modular image-processing API that combines secure user authentication, flexible image transformations, reliable file management, and scalable background processing.

The project will prioritize correctness, maintainability, and practical engineering decisions over unnecessary complexity. Each infrastructure upgrade will be introduced when it solves a demonstrated limitation or enables a concrete feature.
