import uuid
import warnings
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool
from PIL import Image, UnidentifiedImageError


BASE_DIR = Path(__file__).resolve().parent.parent.parent / "storage"

ORIGINAL_DIR = BASE_DIR / "original"
TRANSFORMED_DIR = BASE_DIR / "transformed"

ORIGINAL_DIR.mkdir(parents=True, exist_ok=True)
TRANSFORMED_DIR.mkdir(parents=True, exist_ok=True)


MAX_SIZE = 10 * 1024 * 1024 
CHUNK_SIZE = 1024 * 1024  

MAX_WIDTH = 10_000
MAX_HEIGHT = 10_000
MAX_PIXELS = 50_000_000

Image.MAX_IMAGE_PIXELS = MAX_PIXELS

ALLOWED_TYPES = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}

# What it does: It pulls the uploaded file into server memory 1 MB at a time.
#If at any point the running total crosses 10 MB  it raises an instant 413 Payload Too Large error.
#If the file is safe, it fuses the chunks back together using b"".join(chunks) and returns the raw file bytes.
async def read_with_limit(file: UploadFile,limit: int = MAX_SIZE) -> bytes:
    chunks = []
    size = 0

    while chunk := await file.read(CHUNK_SIZE):
        size += len(chunk)

        if size > limit:
            raise HTTPException(
                status_code=413,
                detail="File too large (maximum 10 MiB)",
            )

        chunks.append(chunk)

    return b"".join(chunks)

