from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.constants import MAX_UPLOAD_SIZE_MB, UPLOAD_PATH, ACCESS_TOKEN_EXPIRE_MINUTES

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    
    jwt_secret: str
    database_url: str
    redis_url: str
    upload_path: str = UPLOAD_PATH
    max_upload_size_mb: int = MAX_UPLOAD_SIZE_MB
    access_token_expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES

settings = Settings()