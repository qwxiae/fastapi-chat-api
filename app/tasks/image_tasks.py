from PIL import Image
from app.core.celery_app import celery_app
from app.core.constants import AVATAR_SIZE

@celery_app.task(name="process_avatar")
def process_avatar(file_path: str) -> str:
    """
    Resize to a standard square size.
    Runs in a Celery worker process
    """
    image = Image.open(file_path)
    if image.mode not in ("RGB", "L"):
        image.convert("RGB")
    
    image.thumbnail(AVATAR_SIZE)
    image.save(file_path)
    return file_path