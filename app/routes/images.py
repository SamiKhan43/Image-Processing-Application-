from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
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
    ResizeImageRequest
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
    image_data = await save_original_image(file)

    image_record = ImageMetaData(
        user_id=current_user.id,
        original_filename=image_data["filename"],
        file_path=image_data["file_path"],
        format=image_data["format"],
        width=image_data["width"],
        height=image_data["height"],
    )

    try :
        db.add(resized_record)
        db.commit()
        db.refresh(resized_record)
    except SQLAlchemyError :
        try:
            delete_file(Path(result["file_path"]))
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save resized image metadata",
        ) from e

    return {
        "message": "Image uploaded successfully",
        "image_id": image_record.id,
        "original_filename": image_record.original_filename,
        "format": image_record.format,
        "width": image_record.width,
        "height": image_record.height,
        "file_size": image_data["size"],
        "created_at": image_record.created_at,
    }

@router.post("/{image_id}/resize", status_code=201)
def resize_existing_image(
    image_id : int ,
    request : ResizeImageRequest,
    db : Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original_record = db.query(ImageMetaData).filter(
        ImageMetaData.id == image_id,
        ImageMetaData.user_id == current_user.id,
    ).first()

    if original_record is None :
        raise HTTPException(
            status_code=404,
            detail= "image not found",
        )

    resized_image = resize_image(
        filename=original_record.original_filename,
        width=request.width,
        height=request.height,
    )

    resized_record = ImageMetaData(
        user_id=current_user.id,
        original_filename=result["filename"],
        file_path=result["file_path"],
        format=result["format"],
        width=result["width"],
        height=result["height"],
    )

    try :
        db.add(resized_record)
        db.commit()
        db.refresh(resized_record)
    except SQLAlchemyError :
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
        "image_id": resized_record.id,
        "source_image_id": original_record.id,
        "filename": resized_record.original_filename,
        "format": resized_record.format,
        "width": resized_record.width,
        "height": resized_record.height,
        "file_size": result["file_size"],
    }
