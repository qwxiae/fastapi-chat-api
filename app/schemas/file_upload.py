from pydantic import BaseModel
from datetime import datetime


class FileUploadResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    file_type: str
    file_size_kb: int
    user_id: str
    room_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}