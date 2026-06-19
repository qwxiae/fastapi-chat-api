import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[str]  = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    room_id: Mapped[str]  = mapped_column(String(36), ForeignKey("rooms.id"), nullable=False)
    send_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=True)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())