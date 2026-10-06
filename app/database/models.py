from datetime import datetime 
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = "users"

    # Primary key for each user
    id : Mapped[int] = mapped_column(Integer , primary_key=True ,index=True)
    username : Mapped[str] = mapped_column(String ,unique = True ,index = True , nullable = False)
    hashed_password : Mapped[str] = mapped_column(String , nullable = False)

    # One user can have many images 
    # Deleting a user also deletes their image metadata
    images: Mapped[list["ImageMetadata"]] = relationship("ImageMetadata", back_populates="owner", cascade="all, delete-orphan")

class ImageMetaData(Base):
    __tablename__ = "image_metadata"

    # Primary key for each image record
    id : Mapped[int] = mapped_column(Integer , primary_key = True , index = True)

    # Connects this image to its owner in the users table
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


    original_filename : Mapped[str] = mapped_column(String , nullable = False)
    file_path : Mapped[str] = mapped_column(String , nullable = False)

    # Image format such as PNG, JPEG, or WEBP
    format : Mapped[str] = mapped_column(String , nullable = False)

    #Image dimensions
    width : Mapped[int] = mapped_column(Integer , nullable = True)
    hieght : Mapped[int] = mapped_column(Integer , nullable = True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Connect this image back to its User
    owner: Mapped["User"] = relationship("User", back_populates="images")
