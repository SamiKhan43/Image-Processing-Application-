from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import (
    get_current_user,
    hash_password,
    verify_password,
    create_access_token,
)
from app.database.connection import get_db
from app.database.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    hashed = hash_password(user.password)

    new_user = User(
        username=user.username,
        hashed_password=hashed,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": f"User '{user.username}' created successfully"}


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(db_user.username)

    return {
        "access_token": token,
        "token_type": "bearer",
    }