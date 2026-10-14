import uuid

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

from app.services.storage import (
    get_original_path,
    get_transformed_path,
)


def resize_image(
    filename: str,
    width: int,
    height: int,
) -> dict:

    if width <= 0 or height <= 0:
        raise HTTPException(
            status_code=400,
            detail="Width and height must be positive",
        )

    if width > 10000 or height > 10000:
        raise HTTPException(
            status_code=400,
            detail="Width and height cannot exceed 10000 pixels",
        )

    original_path = get_original_path(filename)

    if not original_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Image not found",
        )

    output_filename = f"{uuid.uuid4().hex}.webp"
    output_path = get_transformed_path(output_filename)

    try:
        with Image.open(original_path) as img:
            img = ImageOps.exif_transpose(img)
            img.load()

            resized_img = img.resize((width, height))

            resized_img.save(output_path, format="WEBP")

    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(
            status_code=400,
            detail="Could not process the image",
        ) from e

    return {
        "filename": output_filename,
        "width": width,
        "height": height,
        "format": "WEBP",
        "file_size": output_path.stat().st_size,
    }
