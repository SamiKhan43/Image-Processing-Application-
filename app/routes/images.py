from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import get_db
from app.database.models import User, ImageMetaData
from app.core.security import get_current_user
from app.services.storage import save_original_image, delete_file


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

    try:
        db.add(image_record)
        db.commit()
        db.refresh(image_record)

    except SQLAlchemyError as e:
        db.rollback()

        # Delete the uploaded file if saving its metadata fails.
        delete_file(Path(image_data["file_path"]))

        raise HTTPException(
            status_code=500,
            detail="Could not save image metadata",
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