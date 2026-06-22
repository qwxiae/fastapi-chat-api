from datetime import datetime

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    thumbnail_path: str | None
    file_type: str
    file_size_kb: int
    user_id: str
    room_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
