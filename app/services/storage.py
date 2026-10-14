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
