# Pictura --- Target Architecture & Learning Roadmap

This document outlines the target architecture, explains each component, and provides a recommended learning and implementation order.

> **Note:** Build the core application first and introduce additional technologies as needed.
## 1. Target Architecture

``` mermaid
flowchart TD
    Client["Client Application"]
    Proxy["Reverse Proxy / HTTPS"]
    API["FastAPI Application"]

    Auth["Authentication & Authorization"]
    RateLimit["Rate Limiting"]
    Cache["Redis Cache"]

    DB[("PostgreSQL")]
    Storage["Storage Interface"]
    S3[("S3-Compatible Object Storage")]

    Broker[["Task Queue / Message Broker"]]
    Worker["Background Worker"]
    Processor["Pillow Processing Engine"]
    Jobs[("Job Status in PostgreSQL")]
    Monitoring["Logging & Monitoring"]

    Client --> Proxy
    Proxy --> API
    API --> Auth
    API --> RateLimit
    API --> Cache
    API --> DB
    API --> Storage
    Storage --> S3
    API -->|"Submit processing job"| Broker
    Broker --> Worker
    Worker --> Processor
    Worker --> Storage
    Worker --> Jobs
    API --> Monitoring
    Worker --> Monitoring
```

### Target architecture at a glance

-   **Client:** Sends HTTP requests and receives results.
-   **Reverse proxy:** Handles incoming traffic and may terminate HTTPS
    before forwarding requests to FastAPI.
-   **FastAPI:** Validates requests and coordinates application
    operations.
-   **Authentication and authorization:** Identifies users and checks
    what resources they can access.
-   **PostgreSQL:** Stores persistent application data and
    processing-job records.
-   **Storage interface:** Keeps application logic independent of the
    storage provider.
-   **Object storage:** Stores original and transformed image files in a
    shared location.
-   **Pillow:** Performs image transformations.
-   **Task queue and workers:** Run longer processing jobs outside the
    main request-response cycle.
-   **Redis:** Can provide caching, shared rate-limit state, and a
    Celery broker when configured for that purpose.
-   **Logging and monitoring:** Help diagnose errors and measure
    performance.
-   **CI/CD:** Automatically tests and checks changes, and can later
    automate deployment.
-   **Docker:** Packages the application and its supporting services
    into repeatable environments.

Not every request uses every component. A request to retrieve image
metadata may only need FastAPI, authorization, PostgreSQL, and possibly
a cache. It does not necessarily need Pillow or a background worker.

## 2. Components: Responsibilities, Timing, and Learning Topics

### 2.1 Client Application

**Purpose:** Sends requests to Pictura and displays or uses the results.
It can be a browser, mobile app, frontend, or another service.

Example request:

``` http
POST /images/123/resize
Authorization: Bearer <access_token>
Content-Type: application/json
```

``` json
{
  "width": 800,
  "height": 600
}
```

The client does not need to know how Pillow works, which database is
used, or where image files are stored.

**Learn:** HTTP requests and responses, JSON, status codes, headers,
bearer authentication, and REST API design.

### 2.2 Reverse Proxy and HTTPS

**Possible technologies:** Nginx, Caddy, or a hosting platform's managed
proxy.

**Purpose:** Receives external traffic and forwards it to the
application. Depending on the setup, it can handle HTTPS termination,
request-size limits, and traffic forwarding.

``` text
Client -- HTTPS --> Reverse Proxy -- Internal HTTP --> FastAPI
```

A reverse proxy is not required for local development. Many hosting
platforms provide similar functionality.

**Learn after:** HTTP, FastAPI, and basic Docker deployment.

**Learn:** DNS and domain names, HTTPS and TLS certificates, reverse
proxies, and basic Nginx or Caddy configuration.

### 2.3 FastAPI Application

**Technologies:** FastAPI, Pydantic, Uvicorn.

**Purpose:** Receives requests, validates inputs, invokes application
logic, and returns HTTP responses. Routes should coordinate operations
rather than contain all processing and database logic themselves.

A possible structure:

``` text
app/
├── main.py
├── core/
│   ├── config.py
│   └── security.py
├── routes/
│   ├── auth.py
│   ├── images.py
│   └── jobs.py
├── schemas/
├── services/
├── database/
├── workers/
└── tests/
```

  Directory     Responsibility
  ------------- -------------------------------------------
  `core/`       Configuration and security utilities
  `routes/`     HTTP endpoints and request coordination
  `schemas/`    Request and response validation
  `services/`   Business logic and application operations
  `database/`   Database connections and models
  `workers/`    Background task definitions
  `tests/`      Automated tests

**Learn now:** Request and response models, dependency injection,
routers, service-layer design, exception handling, middleware, and
application lifecycle.

### 2.4 Authentication and Authorization

**Technologies:** JWT, Argon2 password hashing, FastAPI security
utilities.

-   **Authentication:** Establishes who the user is.
-   **Authorization:** Checks whether that user may perform a specific
    action.

For example, if User A owns an image, User B must not be allowed to
retrieve or delete it merely because User B has a valid JWT. Every
protected resource operation must enforce the appropriate ownership or
permission check.

**Learn in this order:**

1.  Password hashing.
2.  JWT structure and expiration.
3.  Access-token validation.
4.  Resource ownership checks.
5.  Refresh tokens.
6.  Token rotation and revocation.
7.  API-key authentication and permissions.

Finish and test basic access-token authentication before adding more
complex session features.

### 2.5 PostgreSQL and Alembic

**Technologies:** PostgreSQL, SQLAlchemy, Alembic.

**Purpose:** Stores persistent application data. Pictura may need tables
for users, image metadata, and processing jobs.

Example conceptual tables:

**`users`**

  Column              Purpose
  ------------------- ------------------------
  `id`                Unique user identifier
  `username`          User's username
  `hashed_password`   Hashed password

**`images`**

  Column                Purpose
  --------------------- -------------------------------------------
  `id`                  Unique image identifier
  `user_id`             Image owner
  `storage_key`         Identifier used to locate the stored file
  `original_filename`   Original filename
  `format`              Image format
  `created_at`          Upload timestamp

**`processing_jobs`**

  Column            Purpose
  ----------------- ---------------------------------
  `id`              Unique job identifier
  `user_id`         User who submitted the job
  `image_id`        Image being processed
  `status`          Current job status
  `operation`       Requested transformation
  `result_key`      Location of the processed image
  `error_message`   Relevant failure information

SQLite is a reasonable starting point. PostgreSQL becomes useful when
you need a database server and its concurrency, operational, and
deployment capabilities. It is not automatically faster for every
workload.

Alembic manages schema changes through versioned migrations rather than
requiring tables to be recreated manually.

**Learn in this order:** SQL fundamentals, primary and foreign keys,
relationships and indexes, transactions, PostgreSQL, SQLAlchemy
sessions, Alembic migrations, and database backup/recovery.

### 2.6 Storage Interface and Object Storage

**Technologies:** Python `Protocol` or abstract base classes, local
filesystem, AWS S3 or another S3-compatible service such as Cloudflare
R2 or MinIO.

**Purpose:** Stores original and transformed image files.

Local storage is suitable during development. However, separate
application instances may have separate local disks, so an image saved
by one instance might not be available to another.

``` text
FastAPI Instance A ----\
                        +---- Shared Object Storage
FastAPI Instance B ----/
```

A storage interface separates the application's storage operations from
their implementation. For example, the application might depend on
`save`, `get`, and `delete` operations while a local-storage
implementation and an S3 implementation perform those operations
differently.

Conceptual illustration only:

``` python
class StorageService:
    def save(self, file, key):
        pass

    def get(self, key):
        pass

    def delete(self, key):
        pass
```

For production code, define a proper interface with a `Protocol` or
abstract base class and clear input/output types.

**Learn in this order:** Python file handling and `pathlib`,
upload/download handling, storage abstraction, object-storage concepts,
buckets and object keys, credentials and permissions, presigned URLs,
and cleanup of stored files.

Start with local storage and add a cloud backend when you can clearly
separate storage logic from the rest of the application.

### 2.7 Pillow Processing Engine

**Technology:** Pillow.

**Purpose:** Performs image transformations such as resizing, cropping,
rotation, flipping, filters, watermarks, format conversion, thumbnails,
and output-quality adjustments.

Keep processing functions independent of FastAPI where possible. This
makes them easier to test and reuse.

A short operation may be handled within a normal request. A long-running
operation or batch may be better suited to a background worker.

Making a route `async` does not automatically make CPU-intensive Pillow
operations non-blocking. Separate worker processes are often more
suitable for heavy processing.

**Learn now:** Finish the processing functions, validate their
parameters, handle invalid images safely, and write unit tests before
adding Celery.

### 2.8 Redis

**Technology:** Redis.

**Purpose:** Redis can serve several roles, but each should be added for
a clear reason.

1.  **Caching:** Stores suitable frequently requested data to reduce
    repeated work.
2.  **Rate limiting:** Stores shared counters when multiple API
    instances need consistent limits.
3.  **Task broker:** Can carry Celery task messages when configured as
    the broker.

Caching requires a plan for expiration and invalidation. Do not cache
private user data without appropriate isolation. Redis is not the only
broker option; RabbitMQ is another common choice for Celery.

**Learn after:** Core API behavior, database operations, and storage are
reliable.

**Learn:** Cache keys, expiration, invalidation, Redis data structures,
shared rate-limit state, and broker concepts.

### 2.9 Celery and Background Workers

**Technologies:** Celery with Redis or RabbitMQ.

**Purpose:** Executes longer-running work outside the main HTTP
request-response cycle.

Example flow:

``` text
Client
  |
  v
FastAPI
  | Submit job
  v
Message Broker
  |
  v
Celery Worker
  |
  v
Pillow Processing
  |
  v
Object Storage
  |
  v
Update Job Status
```

The API might return `202 Accepted` after accepting a job:

``` json
{
  "job_id": "job-123",
  "status": "pending"
}
```

The client can check `GET /jobs/job-123` later. A `202 Accepted`
response means the request has been accepted for processing, not that
processing has finished.

**Learn in this order:**

1.  Synchronous versus asynchronous execution.
2.  Threads versus processes.
3.  Background-task concepts.
4.  Queues and message brokers.
5.  Celery tasks.
6.  Job-status tracking.
7.  Retries and failure handling.
8.  Idempotency and duplicate execution.

Introduce workers after image upload, storage, transformation,
retrieval, and deletion work reliably.

### 2.10 Rate Limiting

**Possible technologies:** SlowAPI or another rate-limiting library;
Redis if shared state is needed.

**Purpose:** Limits how frequently a client can make requests. Login
attempts and expensive image-processing submissions may need stricter
limits than metadata reads.

Start with a simple implementation. Introduce shared Redis-backed limits
if you run multiple application instances or require shared counters.

**Learn after:** HTTP, middleware, and application security.

### 2.11 Automated Testing

**Technologies:** pytest and FastAPI testing utilities.

**Purpose:** Verifies that features work correctly and that future
changes do not break existing behavior.

Tests should cover:

-   Registration and login.
-   Password hashing and token validation.
-   Image uploads and invalid file types.
-   Image transformations.
-   Database operations.
-   Ownership and access control.
-   Deletion and cleanup.
-   Background-job failures.

For example, test that User B cannot retrieve or delete an image owned
by User A.

**Start now:** Write tests as you implement features. Use an isolated
test database and keep tests repeatable.

### 2.12 Logging and Monitoring

**Technologies:** Python logging, structured JSON logs, optional
OpenTelemetry.

**Purpose:** Helps diagnose errors and understand performance. Useful
fields can include a request ID, job ID, operation, processing duration,
and error type.

Never log passwords, access tokens, or sensitive image contents.

Start with consistent application logs and request IDs. Add metrics and
distributed tracing when the application has enough components to
benefit from them.

**Learn:** Python logging, log levels, structured logs, request IDs,
application metrics, and then distributed tracing.

### 2.13 Docker and Deployment

**Technologies:** Docker and Docker Compose.

**Purpose:** Packages the application and runs supporting services in a
repeatable environment.

A possible development environment:

``` text
Docker Compose
      |
      ├── FastAPI
      ├── Celery Worker
      ├── PostgreSQL
      └── Redis
```

Object storage may be an external managed service rather than a local
container.

Docker Compose is useful for local multi-service development. It does
not automatically make an application highly available or
production-ready.

**Learn:** Images and containers, Dockerfiles, environment variables,
volumes, networks, Compose, multi-service applications, production
secrets, deployment, and backups.

### 2.14 CI/CD

**Technology:** GitHub Actions.

**Purpose:** Automatically checks code and can later automate
deployment.

A basic pipeline might be:

``` text
Push to GitHub
      |
      v
Run Ruff
      |
      v
Run pytest
      |
      v
Build Docker Image
      |
      v
Deploy (when configured)
```

Start with automated tests and linting. Add deployment automation once a
stable deployment environment exists.

### 2.15 Kubernetes

**Technologies:** Kubernetes and optionally Helm.

**Purpose:** Orchestrates containers across a cluster and can manage
replicas, service discovery, health checks, rolling updates, and
resource allocation.

Kubernetes adds significant operational complexity. Docker Compose and a
suitable hosting platform may be enough for Pictura for a long time.

**Learn last:** First understand Docker, networking, deployment,
monitoring, and the operational needs of a multi-service application.
Kubernetes is optional, not a requirement for a strong backend project.

## 3. Complete Request Lifecycle

Scenario: a user uploads an image and requests a resize operation.

1.  **Request arrives:** The client sends the image and transformation
    parameters. If configured, a reverse proxy handles HTTPS and
    forwards the request.
2.  **Validation:** FastAPI validates the request, file-size limits, and
    transformation parameters.
3.  **Authentication:** The application validates the user's access
    token.
4.  **Authorization:** Pictura verifies that the user may access the
    relevant image.
5.  **Storage and metadata:** The application saves the image through
    the storage service and stores its metadata in the database.
6.  **Processing decision:** A short operation may run in the request.
    An expensive operation can be submitted to a task queue.
7.  **Worker execution:** A worker runs the Pillow transformation, saves
    the result, and updates the job status.
8.  **Result retrieval:** The client checks job status or receives a
    webhook notification. It then retrieves the result through an
    authorized endpoint or another secure delivery mechanism.
9.  **Monitoring:** Logs and metrics help diagnose failures and slow
    operations.

Not every request requires every component. For example, a metadata
lookup may only need FastAPI, authorization, PostgreSQL, and optionally
Redis.

## 4. Recommended Learning and Implementation Order

  -----------------------------------------------------------------------
  Stage                   Learn                   Build or Deliver
  ----------------------- ----------------------- -----------------------
  1                       HTTP, REST, FastAPI,    Complete core API
                          Pydantic                routes

  2                       Python functions,       Finish and test image
                          Pillow, file handling   transformations

  3                       SQL, SQLAlchemy,        Complete image metadata
                          relationships           and CRUD

  4                       JWT, authorization,     Secure all
                          password hashing        user-specific endpoints

  5                       pytest, mocking,        Build a reliable test
                          integration tests       suite

  6                       Logging, exception      Improve reliability and
                          handling, validation    diagnostics

  7                       Docker, volumes,        Run Pictura
                          environment variables   consistently in
                                                  containers

  8                       PostgreSQL,             Migrate the database
                          transactions, Alembic   

  9                       Storage abstractions    Add cloud-compatible
                          and S3                  file storage

  10                      Redis, caching, rate    Add caching or shared
                          limiting                state where useful

  11                      Processes, queues,      Introduce asynchronous
                          Celery                  image processing

  12                      Job states, retries,    Make background
                          idempotency             processing reliable

  13                      GitHub Actions, CI/CD   Automate tests and
                                                  quality checks

  14                      Deployment, HTTPS,      Deploy the application
                          reverse proxies         

  15                      Metrics, tracing,       Improve production
                          monitoring              observability

  16                      Kubernetes and Helm     Explore orchestration
                                                  if justified
  -----------------------------------------------------------------------

Some topics should be learned in parallel. In particular, testing should
start while the core API is being developed rather than waiting until
Stage 5.

### Immediate next steps for Pictura

1.  Finish the core image-processing functions and test them.
2.  Implement image metadata retrieval, listing, and deletion, including
    ownership checks.
3.  Add pytest tests for authentication, image operations, invalid
    inputs, and authorization.
4.  Improve validation, error handling, and logging.
5.  Continue learning Docker and run the application in containers.
6.  Learn PostgreSQL and Alembic, then migrate when comfortable with the
    existing models.
7.  Add a storage interface and integrate S3-compatible object storage.
8.  Introduce Redis and Celery when longer-running image-processing
    tasks justify them.

## 5. What to Delay

  -----------------------------------------------------------------------
  Technology or concept               Why it can wait
  ----------------------------------- -----------------------------------
  Kubernetes                          Requires a solid understanding of
                                      containers, networking, and
                                      deployment

  Apache Kafka                        Most useful when there is a real
                                      event-streaming requirement

  Microservices                       Adds communication and operational
                                      complexity that a modular monolith
                                      may not need

  Distributed tracing                 Easier to justify once requests
                                      cross multiple services

  Complex caching                     Requires a clear strategy for
                                      invalidation and correctness

  Multiple storage providers          First establish a reliable storage
                                      interface and one working backend

  Advanced token revocation systems   First implement and test basic
                                      authentication correctly
  -----------------------------------------------------------------------

## 6. Architectural Principle

Start with a **modular monolith**: one FastAPI application with clear
boundaries between routes, services, database operations, storage, and
image processing. Add a separate worker and external services when a
concrete requirement justifies them.

The objective is not to use every technology in the diagram. It is to
understand which problem each component solves, what trade-offs it
introduces, and when it becomes worthwhile.
