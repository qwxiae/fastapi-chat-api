import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.constants import ALLOWED_FILE_TYPES, ALLOWED_IMAGE_TYPES


@dataclass
class SavedFile:
    url: str
    path: str
    filename: str
    content_type: str
    size_kb: int


def _save_file(
    contents: bytes, folder: str, original_filename: str | None, content_type: str
) -> SavedFile:
    """Save bytes to disk, return the public URL path"""
    ext = Path(original_filename).suffix.lstrip(".") if original_filename else "bin"
    filename = f"{uuid.uuid4()}.{ext}"
    directory = Path(settings.upload_path) / folder
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / filename
    file_path.write_bytes(contents)

    with open(file_path, "wb") as f:
        f.write(contents)

    return SavedFile(
        url=f"/uploads/{folder}/{filename}",
        path=str(file_path),
        filename=original_filename or filename,
        content_type=content_type,
        size_kb=len(contents) // 1024,
    )


async def _read_and_validate(
    file: UploadFile,
    allowed_types: set[str],
) -> bytes:
    """Read file, validate type and size. Return raw bytes."""
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type not allowed. Allowed: {allowed_types}",
        )

    contents = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.max_upload_size_mb}MB",
        )

    return contents


async def save_avatar(file: UploadFile) -> SavedFile:
    """Validate and save a user or room avatar. Returns public URL."""
    contents = await _read_and_validate(file, ALLOWED_IMAGE_TYPES)
    return _save_file(contents, "avatars", file.filename, file.content_type)


async def save_room_file(file: UploadFile) -> SavedFile:
    """Validate and save a file uploaded to a room.  Returns public URL."""
    contents = await _read_and_validate(file, ALLOWED_FILE_TYPES)
    return _save_file(contents, "rooms", file.filename, file.content_type)
