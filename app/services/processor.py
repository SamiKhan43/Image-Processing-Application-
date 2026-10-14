import uuid
import math

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


def crop_image(
    filename: str,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> dict:

    if left < 0 or top < 0:
        raise HTTPException(
            status_code=400,
            detail="Coordinates cannot be negative",
        )

    if left >= right:
        raise HTTPException(
            status_code=400,
            detail="Left must be smaller than right",
        )

    if top >= bottom:
        raise HTTPException(
            status_code=400,
            detail="Top must be smaller than bottom",
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

            if right > img.width or bottom > img.height:
                raise HTTPException(
                    status_code=400,
                    detail="Crop coordinates exceed image dimensions",
                )

            cropped_image = img.crop(
                (left, top, right, bottom)
            )

            if cropped_image.mode not in ("RGB", "RGBA"):
                has_transparency = (
                    "A" in cropped_image.getbands()
                    or "transparency" in cropped_image.info
                )

                cropped_image = cropped_image.convert(
                    "RGBA" if has_transparency else "RGB"
                )

            cropped_image.save(output_path, format="WEBP")

    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(
            status_code=400,
            detail="Could not process the image",
        ) from e

    return {
        "filename": output_filename,
        "file_path": str(output_path),
        "width": cropped_image.width,
        "height": cropped_image.height,
        "format": "WEBP",
    }

def rotate_image(filename: str, degrees: int) -> dict:
    if isinstance(degrees, bool) or not isinstance(degrees, int):
        raise HTTPException(
            status_code=400,
            detail="Degrees must be an integer",
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

            rotated_image = img.rotate(degrees, expand=True)

            if (
                rotated_image.width > 10000
                or rotated_image.height > 10000
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Rotated image dimensions exceed 10000 pixels",
                )

            rotated_image.save(output_path, format="WEBP")

    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(
            status_code=400,
            detail="Could not process the image",
        ) from e

    return {
        "filename": output_filename,
        "file_path": str(output_path),
        "width": rotated_image.width,
        "height": rotated_image.height,
        "format": "WEBP",
        "file_size": output_path.stat().st_size,
    }

def flip_image(
    filename: str,
    horizontal: bool,
    vertical: bool,
) -> dict:

    if not isinstance(horizontal, bool) or not isinstance(vertical, bool):
        raise HTTPException(
            status_code=400,
            detail="Horizontal and vertical must be boolean values",
        )

    if not horizontal and not vertical:
        raise HTTPException(
            status_code=400,
            detail="At least one of horizontal or vertical must be True",
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

            flipped_image = img

            if horizontal:
                flipped_image = flipped_image.transpose(
                    Image.Transpose.FLIP_LEFT_RIGHT
                )

            if vertical:
                flipped_image = flipped_image.transpose(
                    Image.Transpose.FLIP_TOP_BOTTOM
                )

            if flipped_image.mode not in ("RGB", "RGBA"):
                has_transparency = (
                    "A" in flipped_image.getbands()
                    or "transparency" in flipped_image.info
                )

                flipped_image = flipped_image.convert(
                    "RGBA" if has_transparency else "RGB"
                )

            flipped_image.save(output_path, format="WEBP")

    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(
            status_code=400,
            detail="Could not process the image",
        ) from e

    return {
        "filename": output_filename,
        "file_path": str(output_path),
        "width": flipped_image.width,
        "height": flipped_image.height,
        "format": "WEBP",
        "file_size": output_path.stat().st_size,
    }
