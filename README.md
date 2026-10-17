# Pictura

[README](./README.md) | [MIT License](./LICENSE) | [ROADMAP](./ROADMAP.md)

> A secure, JWT-protected REST API for uploading images and transforming them: resize, crop, rotate, flip, watermark, compress, convert and filter.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)
![SQLite](https://img.shields.io/badge/database-SQLite-lightgrey)
![Docker](https://img.shields.io/badge/docker-ready-2496ED)
![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC)

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Quick start](#quick-start)
- [Run with Docker](#run-with-docker)
- [Using the API](#using-the-api)
- [API reference](#api-reference)
- [Configuration](#configuration)
- [Testing](#testing)
- [Project structure](#project-structure)
- [Security notes](#security-notes)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)

## Overview

Pictura is a small, focused image-processing backend built with FastAPI, SQLAlchemy and Pillow. Users sign up, log in to get a JWT, upload images, and apply transformations. Every transformation p[...]

Interactive API docs are served at `/docs` while the server is running.

## Features

- **JWT authentication** with 30-minute access tokens
- **Argon2 password hashing**
- **Safe uploads**: JPEG, PNG and WEBP only, 10 MiB maximum, content verified with Pillow, protection against decompression bombs
- **Per-user isolation**: you can only read and edit your own images
- **Eight transformations**: resize, crop, rotate, flip, watermark, compress, convert, filter
- **Non-destructive editing**: each edit is saved as a new image with a reference to its source
- **Metadata stored per image**: format, dimensions, creation time
- **Health check endpoint** for monitoring and Docker
- **Docker support** with persistent volumes
- **Automated test suite** covering every endpoint

## Quick start

### Prerequisites

- Python 3.9 or newer (the Docker image uses 3.12)
- pip and git

### Install

```bash
git clone https://github.com/SamiKhan43/Image-Processing-Application-.git
cd Image-Processing-Application-

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configure

Create a `.env` file in the project root:

```dotenv
SECRET_KEY="replace-with-a-long-random-string"
```

Generate a strong key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The app refuses to start without `SECRET_KEY`.

### Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000/docs.

## Run with Docker

1. Create a `.env` file next to `docker-compose.yml`:

   ```dotenv
   SECRET_KEY="replace-with-a-long-random-string"
   # PORT=8000   # optional, host port
   ```

2. Build and start:

   ```bash
   docker compose up --build -d
   ```

3. Check that it is healthy:

   ```bash
   docker compose ps
   curl http://localhost:8000/health
   ```

Two named volumes keep your data safe across rebuilds: `database` (the SQLite file) and `image_storage` (uploaded and transformed images).

| Command | What it does |
|---|---|
| `docker compose logs -f api` | Follow the logs |
| `docker compose down` | Stop the app, keep your data |
| `docker compose down -v` | Stop the app and delete the database and images |

## Using the API

A complete flow with `curl`:

```bash
# 1. Sign up
curl -X POST http://127.0.0.1:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"s3cret-pass"}'

# 2. Log in and keep the token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"s3cret-pass"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Upload an image
curl -X POST http://127.0.0.1:8000/images/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@photo.jpg"

# 4. Resize image 1
curl -X POST http://127.0.0.1:8000/images/1/resize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"width":800,"height":600}'

# 5. Download the result (use the image_id from step 4)
curl -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/images/2/file -o result.webp
```

A successful transformation returns `201 Created`:

```json
{
  "message": "Image resized successfully",
  "image_id": 2,
  "source_image_id": 1,
  "filename": "3f9c0e5a....webp",
  "format": "WEBP",
  "width": 800,
  "height": 600,
  "file_size": 18342,
  "created_at": "2026-10-17T10:15:00Z"
}
```

Use the returned `image_id` to chain further edits.

## API reference

All `/images/*` endpoints require the header `Authorization: Bearer <token>`.

| Method | Endpoint | Auth | Description |
|---|---|:---:|---|
| GET | `/` | No | Welcome message |
| GET | `/health` | No | Health check |
| POST | `/auth/signup` | No | Create a user |
| POST | `/auth/login` | No | Get a JWT access token |
| GET | `/auth/profile` | Yes | Current user |
| POST | `/images/upload` | Yes | Upload an image (multipart form, field `file`) |
| GET | `/images/{image_id}/file` | Yes | Download an image you own |
| POST | `/images/{image_id}/resize` | Yes | Resize to width x height |
| POST | `/images/{image_id}/crop` | Yes | Crop to a box |
| POST | `/images/{image_id}/rotate` | Yes | Rotate by degrees |
| POST | `/images/{image_id}/flip` | Yes | Flip horizontally and/or vertically |
| POST | `/images/{image_id}/watermark` | Yes | Add a text watermark |
| POST | `/images/{image_id}/compress` | Yes | Re-encode at a chosen quality |
| POST | `/images/{image_id}/convert` | Yes | Convert to JPEG, PNG or WEBP |
| POST | `/images/{image_id}/filter` | Yes | Apply a named filter |

### Request bodies

| Endpoint | Field | Type | Rules |
|---|---|---|---|
| resize | `width`, `height` | int | 1 to 10,000; total at most 50,000,000 pixels |
| crop | `left`, `top`, `right`, `bottom` | int | `left < right`, `top < bottom`, box must fit inside the image |
| rotate | `degrees` | int | Any integer; result must stay within 10,000 px per side |
| flip | `horizontal`, `vertical` | bool | At least one must be `true` |
| watermark | `watermark_text` | string | 1 to 200 characters |
| | `x`, `y` | int | Top-left position of the text; text must fit inside the image |
| | `font_size` | int | 1 to 500 (default 32) |
| | `opacity` | int | 0 to 255 (default 128) |
| compress | `quality` | int | 0 to 100 (default 80) |
| convert | `target_format` | string | `jpeg` (or `jpg`), `png`, `webp` |
| filter | `filter_name` | string | See the filter list below |
| | `intensity` | int | 1 to 10 (default 1) |

**Available filters:** `blur`, `contour`, `detail`, `edge_enhance`, `edge_enhance_more`, `emboss`, `sharpen`, `smooth`, `smooth_more`, `gaussian_blur`, `unsharp_mask`, `grayscale`, `sepia`.

### Output formats

Resize, crop, rotate, flip, watermark, compress and filter save their result as **WEBP**. Only `convert` lets you choose the output format. Converting a transparent image to JPEG places it on a w[...]

### Status codes

| Code | Meaning |
|---|---|
| 201 | Upload or transformation succeeded |
| 400 | Invalid input: bad crop box, unsupported filter or format, corrupted image, and so on |
| 401 / 403 | Missing, invalid or expired token |
| 404 | Image not found, or it belongs to another user |
| 409 | Username already exists |
| 413 | Upload larger than 10 MiB |
| 422 | Request body failed validation |
| 500 | Could not save the file or its metadata |

## Configuration

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `SECRET_KEY` | Yes | none | Secret used to sign JWTs |
| `DATABASE_URL` | No | `sqlite:///./image_service.db` | SQLAlchemy database URL. Docker sets it to `sqlite:////data/images.db` |
| `PORT` | No | `8000` | Host port used by Docker Compose |

Constants you can change in code:

| Setting | Value | File |
|---|---|---|
| JWT algorithm | HS256 | `app/core/config.py` |
| Token lifetime | 30 minutes | `app/core/config.py` |
| Max upload size | 10 MiB | `app/services/storage.py` |
| Max dimensions | 10,000 px per side, 50M pixels | `app/services/storage.py` |

Add `.env` to `.gitignore` and commit a `.env.example` template instead:

```dotenv
SECRET_KEY="change-me"
```

## Testing

The test suite uses an in-memory database and temporary storage folders, so it never touches your real data.

```bash
pip install pytest httpx
python -m pytest -v
```

It covers authentication, every transformation (on RGB and RGBA images), all filters, chained edits, ownership checks and input validation. Run it from the project root.

## Project structure

```
.
├── .env                  # runtime secrets (not committed)
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── README.md
├── requirements.txt
├── app/
│   ├── main.py           # FastAPI entrypoint, router registration, /health
│   ├── core/
│   │   ├── config.py     # env loading and JWT settings
│   │   └── security.py   # password hashing, JWT helpers, auth dependency
│   ├── database/
│   │   ├── connection.py # engine, session, DATABASE_URL
│   │   └── models.py     # User and ImageMetaData tables
│   ├── routes/
│   │   ├── auth.py       # signup, login, profile
│   │   └── images.py     # upload, download and transformation routes
│   └── services/
│       ├── processor.py  # Pillow image operations
│       └── storage.py    # upload validation and file storage
├── schemas/
│   └── images.py         # request models
└── tests/
    └── test_api.py
```

Created at runtime: the SQLite database file and `storage/original/` and `storage/transformed/`.

## Security notes

- Passwords are hashed with Argon2, never stored in plaintext.
- Keep `SECRET_KEY` private. Anyone who has it can forge tokens.
- Uploads are limited by type, size and pixel count, and the file content is verified rather than trusting the extension.
- Stored filenames are random UUIDs, so user-supplied names never touch the filesystem.
- The Docker image runs as a non-root user.
- Before any public deployment, add HTTPS, rate limiting and stricter password rules.

## Limitations

- SQLite supports a single writer, so run one uvicorn worker. For multiple workers or heavier traffic, point `DATABASE_URL` at PostgreSQL.
- Images are stored on local disk. For multiple servers, move storage to shared or object storage.
- Tables are created on startup. There are no database migrations yet.

## Contributing

1. Fork the repository and create a branch:
   ```bash
   git checkout -b feature/your-feature
   ```
2. Keep routes in `app/routes/` and image logic in `app/services/`.
3. Run `python -m pytest -v` and make sure everything passes.
4. Commit, push, and open a pull request with a clear description.

Please open an issue before starting large changes.

## License
 
This project is licensed under the [MIT License](https://github.com/SamiKhan43/Image-Processing-Application-/blob/main/LICENSE).
 
## Acknowledgements
 
- Project idea: [Image Processing Service](https://roadmap.sh/projects/image-processing-service) on [roadmap.sh](https://roadmap.sh/)
- Built with [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/) and [Pillow](https://python-pillow.org/)
