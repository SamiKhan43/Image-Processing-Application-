from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    username: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    images: Mapped[list["ImageMetaData"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan"
    )


class ImageMetaData(Base):
    __tablename__ = "image_metadata"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    original_filename: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    format: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    width: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    height: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    owner: Mapped["User"] = relationship(back_populates="images")
