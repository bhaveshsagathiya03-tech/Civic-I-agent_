from pathlib import Path
from uuid import uuid4
from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import UploadFile, HTTPException
from ..core.config import settings

ALLOWED_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}

def store_image(upload: UploadFile) -> tuple[str, int, int]:
    settings.media_path.mkdir(parents=True, exist_ok=True)
    max_bytes = settings.max_upload_mb * 1024 * 1024
    payload = upload.file.read(max_bytes + 1)
    if not payload:
        raise HTTPException(400, "The uploaded image is empty.")
    if len(payload) > max_bytes:
        raise HTTPException(413, f"Image exceeds the {settings.max_upload_mb} MB upload limit.")
    try:
        from io import BytesIO
        with Image.open(BytesIO(payload)) as im:
            fmt = im.format
            if fmt not in ALLOWED_FORMATS:
                raise HTTPException(415, "Upload a JPEG, PNG or WEBP image.")
            im.verify()
        with Image.open(BytesIO(payload)) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            width, height = im.size
            if width * height > 25_000_000:
                raise HTTPException(413, "Image dimensions are too large for safe processing.")
            if width < 160 or height < 160:
                raise HTTPException(400, "Image resolution is too small. Upload an image at least 160 x 160 pixels.")
            filename = f"{uuid4().hex}.jpg"
            destination = settings.media_path / filename
            # Re-encode image to remove embedded metadata and avoid trusting original file contents.
            im.save(destination, format="JPEG", quality=92, optimize=True)
            return filename, width, height
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(400, "The uploaded file is not a valid image.") from exc
