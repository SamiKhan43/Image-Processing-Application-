import io
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.connection import Base, get_db
from app.services import storage


@pytest.fixture()
def client(tmp_path, monkeypatch):
    original = tmp_path / "original"
    transformed = tmp_path / "transformed"
    original.mkdir()
    transformed.mkdir()
    monkeypatch.setattr(storage, "ORIGINAL_DIR", original)
    monkeypatch.setattr(storage, "TRANSFORMED_DIR", transformed)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def auth_headers(client, username="alice", password="secret123"):
    client.post("/auth/signup", json={"username": username, "password": password})
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_image(fmt="PNG", mode="RGB", size=(100, 100)):
    color = (200, 50, 50, 255) if mode == "RGBA" else (200, 50, 50)
    buf = io.BytesIO()
    Image.new(mode, size, color).save(buf, format=fmt)
    buf.seek(0)
    return buf


def upload(client, headers, fmt="PNG", mode="RGB"):
    ext = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}[fmt]
    r = client.post(
        "/images/upload",
        headers=headers,
        files={"file": (f"test.{ext}", make_image(fmt, mode), f"image/{ext}")},
    )
    assert r.status_code == 201, r.text
    return r.json()["image_id"]


def test_upload_requires_auth(client):
    r = client.post("/images/upload", files={"file": ("a.png", make_image(), "image/png")})
    assert r.status_code in (401, 403)


def test_signup_duplicate_and_bad_login(client):
    auth_headers(client)
    r = client.post("/auth/signup", json={"username": "alice", "password": "x"})
    assert r.status_code == 409
    r = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
    assert r.status_code == 401


def test_upload_returns_metadata(client):
    h = auth_headers(client)
    r = client.post(
        "/images/upload",
        headers=h,
        files={"file": ("a.png", make_image(size=(120, 80)), "image/png")},
    )
    body = r.json()
    assert r.status_code == 201
    assert body["width"] == 120 and body["height"] == 80
    assert body["format"] == "PNG"
    assert body["file_size"] > 0


def test_upload_rejects_non_image(client):
    h = auth_headers(client)
    r = client.post(
        "/images/upload",
        headers=h,
        files={"file": ("a.png", io.BytesIO(b"not an image"), "image/png")},
    )
    assert r.status_code == 400


EDITS = [
    ("resize", {"width": 50, "height": 40}),
    ("crop", {"left": 0, "top": 0, "right": 30, "bottom": 30}),
    ("rotate", {"degrees": 90}),
    ("flip", {"horizontal": True, "vertical": False}),
    ("watermark", {"watermark_text": "hi", "x": 5, "y": 5, "font_size": 16, "opacity": 200}),
    ("compress", {"quality": 50}),
    ("convert", {"target_format": "jpeg"}),
    ("convert", {"target_format": "png"}),
    ("convert", {"target_format": "webp"}),
]


@pytest.mark.parametrize("mode", ["RGB", "RGBA"])
@pytest.mark.parametrize("endpoint,body", EDITS)
def test_edit_endpoints(client, endpoint, body, mode):
    h = auth_headers(client)
    image_id = upload(client, h, "PNG", mode)
    r = client.post(f"/images/{image_id}/{endpoint}", headers=h, json=body)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["source_image_id"] == image_id
    assert data["image_id"] != image_id
    assert data["file_size"] > 0
    assert "created_at" in data


FILTERS = [
    "blur", "contour", "detail", "edge_enhance", "edge_enhance_more", "emboss",
    "sharpen", "smooth", "smooth_more", "gaussian_blur", "unsharp_mask",
    "grayscale", "sepia",
]


@pytest.mark.parametrize("mode", ["RGB", "RGBA"])
@pytest.mark.parametrize("name", FILTERS)
def test_filters(client, name, mode):
    h = auth_headers(client)
    image_id = upload(client, h, "PNG", mode)
    r = client.post(
        f"/images/{image_id}/filter",
        headers=h,
        json={"filter_name": name, "intensity": 2},
    )
    assert r.status_code == 201, r.text


@pytest.mark.parametrize("fmt", ["JPEG", "WEBP"])
def test_edit_other_source_formats(client, fmt):
    h = auth_headers(client)
    image_id = upload(client, h, fmt)
    r = client.post(f"/images/{image_id}/resize", headers=h, json={"width": 20, "height": 20})
    assert r.status_code == 201, r.text


def test_edit_an_already_edited_image(client):
    h = auth_headers(client)
    image_id = upload(client, h)
    r1 = client.post(f"/images/{image_id}/resize", headers=h, json={"width": 60, "height": 60})
    assert r1.status_code == 201, r1.text
    r2 = client.post(
        f"/images/{r1.json()['image_id']}/crop",
        headers=h,
        json={"left": 0, "top": 0, "right": 20, "bottom": 20},
    )
    assert r2.status_code == 201, r2.text
    assert r2.json()["width"] == 20


def test_other_user_cannot_edit(client):
    alice = auth_headers(client, "alice")
    bob = auth_headers(client, "bob")
    image_id = upload(client, alice)
    r = client.post(f"/images/{image_id}/resize", headers=bob, json={"width": 10, "height": 10})
    assert r.status_code == 404


def test_missing_image_is_404(client):
    h = auth_headers(client)
    r = client.post("/images/9999/rotate", headers=h, json={"degrees": 90})
    assert r.status_code == 404


def test_crop_outside_image_is_400(client):
    h = auth_headers(client)
    image_id = upload(client, h)
    r = client.post(
        f"/images/{image_id}/crop",
        headers=h,
        json={"left": 0, "top": 0, "right": 500, "bottom": 500},
    )
    assert r.status_code == 400


def test_flip_needs_a_direction(client):
    h = auth_headers(client)
    image_id = upload(client, h)
    r = client.post(
        f"/images/{image_id}/flip",
        headers=h,
        json={"horizontal": False, "vertical": False},
    )
    assert r.status_code == 400


def test_unknown_filter_is_400(client):
    h = auth_headers(client)
    image_id = upload(client, h)
    r = client.post(f"/images/{image_id}/filter", headers=h, json={"filter_name": "nope"})
    assert r.status_code == 400


def test_unsupported_convert_format_is_400(client):
    h = auth_headers(client)
    image_id = upload(client, h)
    r = client.post(f"/images/{image_id}/convert", headers=h, json={"target_format": "gif"})
    assert r.status_code == 400


def test_watermark_outside_image_is_400(client):
    h = auth_headers(client)
    image_id = upload(client, h)
    r = client.post(
        f"/images/{image_id}/watermark",
        headers=h,
        json={"watermark_text": "hi", "x": 5000, "y": 5, "font_size": 16, "opacity": 100},
    )
    assert r.status_code == 400


def test_resize_over_limit_is_422(client):
    h = auth_headers(client)
    image_id = upload(client, h)
    r = client.post(f"/images/{image_id}/resize", headers=h, json={"width": 20000, "height": 10})
    assert r.status_code == 422
