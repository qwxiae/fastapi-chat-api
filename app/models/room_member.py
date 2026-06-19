from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class RoomMember(Base):
    __tablename__ = "room_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    room_id: Mapped[str] = mapped_column(String(36), ForeignKey("rooms.id"))
    