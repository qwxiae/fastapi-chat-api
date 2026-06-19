from pydantic import BaseModel
from datetime import datetime

class RoomCreate(BaseModel):
    name: str
    description: str | None = None
    is_private: bool = False


class RoomUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_private: bool | None = None

class RoomResponse(BaseModel):
    id: str
    name: str
    description: str | None
    is_private: bool
    avatar_url: str | None
    owner_id: str
    created_at: datetime

    model_config = {"from_attributes": True}

class RoomMemberResponse(BaseModel):
    user_id: str
    room_id: str
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}
    