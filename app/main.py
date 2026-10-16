from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.connection import Base, engine
import app.database.models
from app.routes import auth, images


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Image Processing Service",
    description="An API for uploading, storing, and transforming images.",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(auth.router)
app.include_router(images.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to the Image Processing Service",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}