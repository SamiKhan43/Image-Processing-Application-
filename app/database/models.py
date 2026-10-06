from sqlalchemy import Column , Integer , String
from database import Base

class User(Base):
    __tablename__ = "users"

    id : Mapped[int] = mapped_column(Integer , primary_key=True ,index=True)
    username : Mapped[str] = mapped_column(String ,unique = True ,index = True , nullable = True)
    hashed_password : Mapped[str] = mapped_column(String , nullable = False)

class ImageMetaData(Base):
    __tablename__ = image_metadata

    id : Mapped[int] = mapped_column(Integer , primary_key = True , index = True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    original_filename : Mapped[str] = mapped_column(String , nullable = False)
    file_path : Mapped[str] = mapped_column(String , nullable = False)

    format : Mapped[str] = mapped_column(String , nullable = False)
    width : Mapped[int] = mapped_column(Integer , nullable = True)
    hieght : Mapped[int] = mapped_column(Integer , nullable = True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    owner: Mapped["User"] = relationship("User", back_populates="images")
