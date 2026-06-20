from pydantic import BaseModel
from datetime import datetime

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: str
    content: str
    user_id: str
    room_id: str
    created_at: datetime

    model_config = {"from_attributes": True}

    