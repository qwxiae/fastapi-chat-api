# IMAGE UPLOADS
UPLOAD_PATH                 ="app/uploads"
MAX_UPLOAD_SIZE_MB          = 20
ACCESS_TOKEN_EXPIRE_MINUTES = 60

ALLOWED_IMAGE_TYPES         = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_FILE_TYPES          = {"application/pdf", "application/zip"} | ALLOWED_IMAGE_TYPES

AVATAR_SIZE                 = (256, 256)
THUMBNAIL_SIZE              = (128, 128)

MESSAGE_HISTORY             = 50    # messages sent to a user on room join
CACHE_TTL_ACCOUNT           = 60    # seconds
CACHE_TTL_MESSAGES          = 30    # seconds

