from PIL import Image, ImageOps
from app.core.celery_app import celery_app
from app.core.constants import AVATAR_SIZE, THUMBNAIL_SIZE

@celery_app.task(name="process_avatar")
def process_avatar(file_path: str) -> str:
    """
    Resize to a standard square size.
    Runs in a Celery worker process
    """
    image = Image.open(file_path)
    if image.mode not in ("RGB", "L"):
        image.convert("RGB")
    
    image = ImageOps.fit(image, AVATAR_SIZE, Image.LANCZOS, centering=(0.5, 0.5))
    image.save(file_path)
    return file_path

@celery_app.task(name="generate_thumbnail")
def generate_thumbnail(file_path: str) -> str:
    """
    Generate a thumbnail for an image file shared in a room.
    Unlike avatars, this preserves aspect ratio.
    """
    from pathlib import Path
    path = Path(file_path)
    thumb_path = path.with_stem(f"{path.stem}_thumb")

    image = Image.open(file_path)
    if image.mode not in ("RGB", L):
        image.convert ("RGB")

    image.thumbnail(THUMBNAIL_SIZE)
    image.save(thumb_path)
    return str(thumb_path)