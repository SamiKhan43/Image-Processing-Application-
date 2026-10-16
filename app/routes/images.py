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

