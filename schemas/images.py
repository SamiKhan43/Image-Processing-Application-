from pydantic import BaseModel, Field


class ResizeImageRequest(BaseModel):
    width: int = Field(gt=0, le=10000)
    height: int = Field(gt=0, le=10000)


class CropImageRequest(BaseModel):
    left: int = Field(ge=0)
    top: int = Field(ge=0)
    right: int = Field(gt=0)
    bottom: int = Field(gt=0)


class RotateImageRequest(BaseModel):
    degrees: int


class FlipImageRequest(BaseModel):
    horizontal: bool = False
    vertical: bool = False


class WatermarkRequest(BaseModel):
    watermark_text: str = Field(min_length=1, max_length=200)
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    font_size: int = Field(default=32, ge=1, le=500)
    opacity: int = Field(default=128, ge=0, le=255)


class CompressImageRequest(BaseModel):
    quality: int = Field(default=80, ge=0, le=100)


class ChangeFormatRequest(BaseModel):
    target_format: str


class FilterImageRequest(BaseModel):
    filter_name: str
    intensity: int = Field(default=1, ge=1, le=10)