from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database.connection import get_db
from app.database.models import User, ImageMetaData
from app.core.security import get_current_user
from app.services.storage import save_original_image, delete_file
from app.services.processor import (
    resize_image,
    crop_image,
    rotate_image,
    flip_image,
    add_watermark,
    compress_image,
    change_format,
    add_filter,
)

from app.schemas.images import (
    ResizeImageRequest,
    CropImageRequest,
    RotateImageRequest,
    FlipImageRequest,
    WatermarkRequest,
    CompressImageRequest,
    ChangeFormatRequest,  
    FilterImageRequest,   
)

router = APIRouter(
    prefix="/images",
    tags=["Images"],
)


@router.post("/upload", status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await save_original_image(file)
 
    new_record = ImageMetaData(
        user_id=current_user.id,
        original_filename=result["filename"],
        file_path=result["file_path"],
        format=result["format"],
        width=result["width"],
        height=result["height"],
    )
 
    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
    except SQLAlchemyError as e:
        db.rollback()
        try:
            delete_file(Path(result["file_path"]))
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save uploaded image metadata",
        ) from e
 
    return {
        "message": "Image uploaded successfully",
        "image_id": new_record.id,
        "filename": new_record.original_filename,
        "format": new_record.format,
        "width": new_record.width,
        "height": new_record.height,
        "file_size": result["size"],
        "created_at": new_record.created_at,
    }



@router.post("/{image_id}/resize", status_code=201)
def resize_existing_image(
    image_id: int,
    request: ResizeImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original_record = db.query(ImageMetaData).filter(
        ImageMetaData.id == image_id,
        ImageMetaData.user_id == current_user.id,
    ).first()

    if original_record is None:
        raise HTTPException(
            status_code=404,
            detail="Image not found",
    )

    result = resize_image(
        filename=original_record.original_filename,
        width=request.width,
        height=request.height,
    )

    new_record = ImageMetaData(
        user_id=current_user.id,
        original_filename=result["filename"],
        file_path=result["file_path"],
        format=result["format"],
        width=result["width"],
        height=result["height"],
    )

    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
    except SQLAlchemyError as e:
        db.rollback()
        try:
            delete_file(Path(result["file_path"]))
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save resized image metadata",
        ) from e

    return {
        "message": "Image resized successfully",
        "image_id": new_record.id,
        "source_image_id": original_record.id,
        "filename": new_record.original_filename,
        "format": new_record.format,
        "width": new_record.width,
        "height": new_record.height,
        "file_size": result["file_size"],
        "created_at": new_record.created_at,
    }

@router.post("/{image_id}/crop", status_code=201)
def crop_existing_image(
    image_id: int,
    request: CropImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original_record = db.query(ImageMetaData).filter(
        ImageMetaData.id == image_id,
        ImageMetaData.user_id == current_user.id,
    ).first()

    if original_record is None:
        raise HTTPException(status_code=404, detail="Image not found")

    result = crop_image(
        filename=original_record.original_filename,
        left=request.left,
        top=request.top,
        right=request.right,
        bottom=request.bottom,
    )

    new_record = ImageMetaData(
        user_id=current_user.id,
        original_filename=result["filename"],
        file_path=result["file_path"],
        format=result["format"],
        width=result["width"],
        height=result["height"],
    )

    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
    except SQLAlchemyError as e:
        db.rollback()
        try:
            delete_file(Path(result["file_path"]))
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save cropped image metadata",
        ) from e

    return {
        "message": "Image cropped successfully",
        "image_id": new_record.id,
        "source_image_id": original_record.id,
        "filename": new_record.original_filename,
        "format": new_record.format,
        "width": new_record.width,
        "height": new_record.height,
        "file_size": result["file_size"],
        "created_at": new_record.created_at,
    }


@router.post("/{image_id}/rotate", status_code=201)
def rotate_existing_image(
    image_id: int,
    request: RotateImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original_record = db.query(ImageMetaData).filter(
        ImageMetaData.id == image_id,
        ImageMetaData.user_id == current_user.id,
    ).first()

    if original_record is None:
        raise HTTPException(status_code=404, detail="Image not found")

    result = rotate_image(
        filename=original_record.original_filename,
        degree=request.degrees,  # check this matches your processor's parameter name
    )

    new_record = ImageMetaData(
        user_id=current_user.id,
        original_filename=result["filename"],
        file_path=result["file_path"],
        format=result["format"],
        width=result["width"],
        height=result["height"],
    )

    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
    except SQLAlchemyError as e:
        db.rollback()
        try:
            delete_file(Path(result["file_path"]))
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save rotated image metadata",
        ) from e

    return {
        "message": "Image rotated successfully",
        "image_id": new_record.id,
        "source_image_id": original_record.id,
        "filename": new_record.original_filename,
        "format": new_record.format,
        "width": new_record.width,
        "height": new_record.height,
        "file_size": result["file_size"],
        "created_at": new_record.created_at,
    }

@router.post("/{image_id}/flip", status_code=201)
def flip_existing_image(
    image_id: int,
    request: FlipImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original_record = db.query(ImageMetaData).filter(
        ImageMetaData.id == image_id,
        ImageMetaData.user_id == current_user.id,
    ).first()

    if original_record is None:
        raise HTTPException(status_code=404, detail="Image not found")

    result = flip_image(
        filename = original_record.original_filename,
        horizontal = request.horizontal,
        vertical = request.vertical
    )

    new_record = ImageMetaData(
        user_id=current_user.id,
        original_filename=result["filename"],
        file_path=result["file_path"],
        format=result["format"],
        width=result["width"],
        height=result["height"],
    )

    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
    except SQLAlchemyError as e:
        db.rollback()
        try:
            delete_file(Path(result["file_path"]))
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save flipped image metadata",
        ) from e

    return {
        "message": "Image flipped successfully",
        "image_id": new_record.id,
        "source_image_id": original_record.id,
        "filename": new_record.original_filename,
        "format": new_record.format,
        "width": new_record.width,
        "height": new_record.height,
        "file_size": result["file_size"],
        "created_at": new_record.created_at,
    }


@router.post("/{image_id}/watermark", status_code=201)
def add_watermark_to_existing_image(
    image_id: int,
    request: WatermarkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original_record = db.query(ImageMetaData).filter(
        ImageMetaData.id == image_id,
        ImageMetaData.user_id == current_user.id,
    ).first()

    if original_record is None:
        raise HTTPException(status_code=404, detail="Image not found")

    result = add_watermark (
        filename = original_record.original_filename,
        watermark_text = request.watermark_text,
        x_cordinate= request.x,
        y_cordinate = request.x,
        font_size = request.font_size,
        opacity = request.opacity
    )

    new_record = ImageMetaData(
        user_id=current_user.id,
        original_filename=result["filename"],
        file_path=result["file_path"],
        format=result["format"],
        width=result["width"],
        height=result["height"],
    )

    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
    except SQLAlchemyError as e:
        db.rollback()
        try:
            delete_file(Path(result["file_path"]))
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save watermarked image metadata",
        ) from e

    return {
        "message": "Watermark added successfully",
        "image_id": new_record.id,
        "source_image_id": original_record.id,
        "filename": new_record.original_filename,
        "format": new_record.format,
        "width": new_record.width,
        "height": new_record.height,
        "file_size": result["file_size"],
        "created_at": new_record.created_at,
    }

@router.post("/{image_id}/compress", status_code=201)
def compress_existing_image(
    image_id: int,
    request: CompressImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original_record = db.query(ImageMetaData).filter(
        ImageMetaData.id == image_id,
        ImageMetaData.user_id == current_user.id,
    ).first()

    if original_record is None:
        raise HTTPException(status_code=404, detail="Image not found")

    result = compress_image(
        filename=original_record.original_filename,
        quality = request.quality
        )

    new_record = ImageMetaData(
        user_id=current_user.id,
        original_filename=result["filename"],
        file_path=result["file_path"],
        format=result["format"],
        width=result["width"],
        height=result["height"],
    )

    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
    except SQLAlchemyError as e:
        db.rollback()
        try:
            delete_file(Path(result["file_path"]))
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save compressed image metadata",
        ) from e

    return {
        "message": "Image compressed successfully",
        "image_id": new_record.id,
        "source_image_id": original_record.id,
        "filename": new_record.original_filename,
        "format": new_record.format,
        "width": new_record.width,
        "height": new_record.height,
        "file_size": result["file_size"],
        "created_at": new_record.created_at,
    }

@router.post("/{image_id}/convert", status_code=201)
def change_format_of_existing_image(
    image_id: int,
    request: ConvertImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original_record = db.query(ImageMetaData).filter(
        ImageMetaData.id == image_id,
        ImageMetaData.user_id == current_user.id,
    ).first()

    if original_record is None:
        raise HTTPException(status_code=404, detail="Image not found")

    result = change_format(
        filename=original_record.original_filename, 
        target_format = request.target_format
    )

    new_record = ImageMetaData(
        user_id=current_user.id,
        original_filename=result["filename"],
        file_path=result["file_path"],
        format=result["format"],
        width=result["width"],
        height=result["height"],
    )

    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
    except SQLAlchemyError as e:
        db.rollback()
        try:
            delete_file(Path(result["file_path"]))
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save converted image metadata",
        ) from e

    return {
        "message": "Image format changed successfully",
        "image_id": new_record.id,
        "source_image_id": original_record.id,
        "filename": new_record.original_filename,
        "format": new_record.format,
        "width": new_record.width,
        "height": new_record.height,
        "file_size": result["file_size"],
        "created_at": new_record.created_at,
    }

