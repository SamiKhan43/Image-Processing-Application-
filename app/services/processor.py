import uuid
import math

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError, ImageDraw, ImageFont

from app.services.storage import (
    MAX_HEIGHT,
    MAX_PIXELS,
    MAX_WIDTH,
    get_original_path,
    get_transformed_path,
    ALLOWED_TYPES
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

    if width > MAX_WIDTH or height > MAX_HEIGHT:
        raise HTTPException(
            status_code=400,
            detail="Width and height cannot exceed 10000 pixels",
        )

    if width * height > MAX_PIXELS:
        raise HTTPException(
            status_code=400,
            detail="Image cannot exceed 50000000 pixels",
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


def add_watermark(
    filename: str,
    watermark_text: str,
    x: int,
    y: int,
    font_size: int = 32,
    opacity: int = 128,
) -> dict:

    if not isinstance(watermark_text, str) or not watermark_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Watermark text cannot be empty",
        )

    if (
        isinstance(opacity, bool)
        or not isinstance(opacity, int)
        or not 0 <= opacity <= 255
    ):
        raise HTTPException(
            status_code=400,
            detail="Opacity must be an integer between 0 and 255",
        )

    if (
        isinstance(x, bool)
        or isinstance(y, bool)
        or not isinstance(x, int)
        or not isinstance(y, int)
    ):
        raise HTTPException(
            status_code=400,
            detail="Coordinates must be integers",
        )

    if x < 0 or y < 0:
        raise HTTPException(
            status_code=400,
            detail="Coordinates cannot be negative",
        )

    if (
        isinstance(font_size, bool)
        or not isinstance(font_size, int)
        or not 1 <= font_size <= 500
    ):
        raise HTTPException(
            status_code=400,
            detail="Font size must be an integer between 1 and 500",
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

            if x >= img.width or y >= img.height:
                raise HTTPException(
                    status_code=400,
                    detail="Watermark coordinates exceed image dimensions",
                )

            watermark_layer = Image.new(
                "RGBA",
                img.size,
                (0, 0, 0, 0),
            )

            draw = ImageDraw.Draw(watermark_layer)
            font = ImageFont.load_default(size=font_size)

            text_bounds = draw.textbbox(
                (x, y),
                watermark_text,
                font=font,
            )

            if text_bounds[2] > img.width or text_bounds[3] > img.height:
                raise HTTPException(
                    status_code=400,
                    detail="Watermark text extends beyond image dimensions",
                )

            draw.text(
                (x, y),
                watermark_text,
                font=font,
                fill=(255, 255, 255, opacity),
            )

            watermarked_image = Image.alpha_composite(
                img.convert("RGBA"),
                watermark_layer,
            )

    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(
            status_code=400,
            detail="Could not process the image",
        ) from e

    try:
        watermarked_image.save(output_path, format="WEBP")
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail="Could not save the watermarked image",
        ) from e

    return {
        "filename": output_filename,
        "file_path": str(output_path),
        "width": watermarked_image.width,
        "height": watermarked_image.height,
        "format": "WEBP",
        "file_size": output_path.stat().st_size,
    }


def compress_image(
    filename: str,
    quality: int = 80,
) -> dict:

    if (
        isinstance(quality, bool)
        or not isinstance(quality, int)
        or not 0 <= quality <= 100
    ):
        raise HTTPException(
            status_code=400,
            detail="Quality must be an integer between 0 and 100",
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

            has_transparency = (
                "A" in img.getbands()
                or "transparency" in img.info
            )

            compressed_image = img.convert(
                "RGBA" if has_transparency else "RGB"
            )

    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(
            status_code=400,
            detail="Could not process the image",
        ) from e

    try:
        compressed_image.save(
            output_path,
            format="WEBP",
            quality=quality,
        )

    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail="Could not save the compressed image",
        ) from e

    return {
        "filename": output_filename,
        "file_path": str(output_path),
        "width": compressed_image.width,
        "height": compressed_image.height,
        "format": "WEBP",
        "file_size": output_path.stat().st_size,
    }


def change_format(
    filename: str,
    target_format: str,
) -> dict:

    if not isinstance(target_format, str):
        raise HTTPException(
            status_code=400,
            detail="Target format must be a string",
        )

    target_format = target_format.strip().upper()

    if target_format == "JPG":
        target_format = "JPEG"

    if target_format not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Target format must be one of {list(ALLOWED_TYPES.keys())}",
        )

    original_path = get_original_path(filename)

    if not original_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Image not found",
        )

    output_filename = f"{uuid.uuid4().hex}{ALLOWED_TYPES[target_format]}"
    output_path = get_transformed_path(output_filename)

    try:
        with Image.open(original_path) as img:
            img = ImageOps.exif_transpose(img)
            img.load()

            has_transparency = (
                "A" in img.getbands()
                or "transparency" in img.info
            )

            if target_format == "JPEG":
                if has_transparency:
                    rgba_image = img.convert("RGBA")

                    converted_image = Image.new(
                        "RGB",
                        rgba_image.size,
                        (255, 255, 255),
                    )

                    converted_image.paste(
                        rgba_image,
                        mask=rgba_image.getchannel("A"),
                    )
                else:
                    converted_image = img.convert("RGB")

            else:
                converted_image = img.convert(
                    "RGBA" if has_transparency else "RGB"
                )

    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(
            status_code=400,
            detail="Could not process the image",
        ) from e

    try:
        converted_image.save(
            output_path,
            format=target_format,
        )

    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail="Could not save the converted image",
        ) from e

    return {
        "filename": output_filename,
        "file_path": str(output_path),
        "width": converted_image.width,
        "height": converted_image.height,
        "format": target_format,
        "file_size": output_path.stat().st_size,
    }


def add_filter(
    filename: str,
    filter_name: str,
    intensity: int = 1,
) -> dict:

    if not isinstance(filter_name, str) or not filter_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Filter name must be a non empty string",
        )

    if (
        isinstance(intensity, bool)
        or not isinstance(intensity, int)
        or not 1 <= intensity <= 10
    ):
        raise HTTPException(
            status_code=400,
            detail="Intensity must be an integer between 1 and 10",
        )

    filter_key = filter_name.strip().upper()

    basic_filters = {
        "BLUR": ImageFilter.BLUR,
        "CONTOUR": ImageFilter.CONTOUR,
        "DETAIL": ImageFilter.DETAIL,
        "EDGE_ENHANCE": ImageFilter.EDGE_ENHANCE,
        "EDGE_ENHANCE_MORE": ImageFilter.EDGE_ENHANCE_MORE,
        "EMBOSS": ImageFilter.EMBOSS,
        "SHARPEN": ImageFilter.SHARPEN,
        "SMOOTH": ImageFilter.SMOOTH,
        "SMOOTH_MORE": ImageFilter.SMOOTH_MORE,
    }

    supported_filters = {
        *basic_filters.keys(),
        "GAUSSIAN_BLUR",
        "UNSHARP_MASK",
        "GRAYSCALE",
        "SEPIA",
    }

    if filter_key not in supported_filters:
        valid = ", ".join(sorted(supported_filters))

        raise HTTPException(
            status_code=400,
            detail=f"Unsupported filter. Supported filters: {valid}",
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

            has_transparency = (
                "A" in img.getbands()
                or "transparency" in img.info
            )

            img = img.convert(
                "RGBA" if has_transparency else "RGB"
            )

            if filter_key in basic_filters:
                filtered_image = img

                for _ in range(intensity):
                    filtered_image = filtered_image.filter(
                        basic_filters[filter_key]
                    )

            elif filter_key == "GAUSSIAN_BLUR":
                filtered_image = img.filter(
                    ImageFilter.GaussianBlur(
                        radius=float(intensity)
                    )
                )

            elif filter_key == "UNSHARP_MASK":
                filtered_image = img.filter(
                    ImageFilter.UnsharpMask(
                        radius=1,
                        percent=intensity * 50,
                    )
                )

            elif filter_key == "GRAYSCALE":
                grayscale = ImageOps.grayscale(img.convert("RGB"))

                if has_transparency:
                    alpha = img.getchannel("A")

                    filtered_image = Image.merge(
                        "RGBA",
                        (grayscale, grayscale, grayscale, alpha),
                    )
                else:
                    filtered_image = grayscale.convert("RGB")

            elif filter_key == "SEPIA":
                grayscale = ImageOps.grayscale(img.convert("RGB"))

                filtered_image = ImageOps.colorize(
                    grayscale,
                    black="#704214",
                    white="#C0A080",
                )

                if has_transparency:
                    filtered_image.putalpha(img.getchannel("A"))

    except (UnidentifiedImageError, OSError, ValueError) as e:
        raise HTTPException(
            status_code=400,
            detail="Could not process the image",
        ) from e

    try:
        filtered_image.save(
            output_path,
            format="WEBP",
        )

    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail="Could not save the filtered image",
        ) from e

    return {
        "filename": output_filename,
        "file_path": str(output_path),
        "width": filtered_image.width,
        "height": filtered_image.height,
        "format": "WEBP",
        "file_size": output_path.stat().st_size,
    }
