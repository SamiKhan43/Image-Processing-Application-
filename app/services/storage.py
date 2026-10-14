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
    
def verify_and_get_metadata(image_bytes: bytes) -> tuple[str, int, int]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter(
                "error",
                Image.DecompressionBombWarning,
            )

            with Image.open(BytesIO(image_bytes)) as img:
                img.verify()

            with Image.open(BytesIO(image_bytes)) as img:
                img_format = img.format

                if img_format not in ALLOWED_TYPES:
                    raise ValueError("Unsupported image format")

                width, height = img.size

                if width > MAX_WIDTH or height > MAX_HEIGHT:
                    raise ValueError("Image dimensions are too large")

                if width * height > MAX_PIXELS:
                    raise ValueError("Image contains too many pixels")

                return img_format, width, height

    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as e:
        raise ValueError("Invalid or corrupted image file") from e
        
async def save_original_image(file: UploadFile) -> dict:
    content = await read_with_limit(file)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Empty file",
        )

    try:
        img_format, width, height = await run_in_threadpool(
            verify_and_get_metadata,
            content,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e

    filename = f"{uuid.uuid4().hex}{ALLOWED_TYPES[img_format]}"
    file_path = ORIGINAL_DIR / filename

    try:
        await run_in_threadpool(file_path.write_bytes, content)
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail="Could not save image",
        ) from e

    return {
        "filename": filename,
        "file_path": str(file_path),
        "format": img_format,
        "width": width,
        "height": height,
        "size": len(content),
    }


def get_original_path(filename: str) -> Path:
    return ORIGINAL_DIR / filename


def get_transformed_path(filename: str) -> Path:
    return TRANSFORMED_DIR / filename


def delete_file(path: Path) -> None:
    path.unlink(missing_ok=True)



