import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi_cache.decorator import cache
from app.core.database import get_db
from app.core.constants import MESSAGE_HISTORY, CACHE_TTL_MESSAGES
from app.dependencies import get_current_user, get_room_membership, PaginationParams, get_pagination
from app.models.message import Message
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse
from app.models.file_upload import FileUpload
from app.schemas.file_upload import FileUploadResponse
from app.services.file_service import save_room_file
from pathlib import Path
import uuid

router = APIRouter(prefix="/rooms", tags=["messages"])

@router.post("/{room_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    room_id: str,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    room: Room = Depends(get_room_membership),
    db: AsyncSession = Depends(get_db),
):
    message = Message(
        id=str(uuid.uuid4()),
        content=payload.content,
        user_id=current_user.id,
        room_id=room_id,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.get("/{room_id}/messages", response_model=list[MessageResponse])
@cache(expire=CACHE_TTL_MESSAGES)
async def list_messages(
    room_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    room: Room = Depends(get_room_membership),
    db: AsyncSession = Depends(get_db),
):
    query = select(Message).where(Message.room_id == room_id)

    if pagination.before:
        cursor_result = await db.execute(select(Message).where(Message.id == pagination.before))
        cursor_message = cursor_result.scalar_one_or_none()
        if cursor_message:
            query = query.where(Message.created_at < cursor_message.created_at)

    query = query.order_by(Message.created_at.desc()).limit(pagination.limit)

    result = await db.execute(query)
    messages = result.scalars().all()
    return list(reversed(messages))


@router.get("/{room_id}/files", response_model=list[FileUploadResponse])
async def list_room_files(
    room_id: str,
    current_user: User = Depends(get_current_user),
    room: Room = Depends(get_room_membership),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FileUpload)
        .where(FileUpload.room_id == room_id)
        .order_by(FileUpload.created_at.desc())
    )
    return result.scalars().all()

@router.post(
    "/{room_id}/files",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_file(
    room_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    room: Room = Depends(get_room_membership),
    db: AsyncSession = Depends(get_db)
):
    saved = await save_room_file(file)

    file_upload = FileUpload(
        id=str(uuid.uuid4()),
        filename=saved.filename,
        file_path=saved.url,
        file_type=saved.content_type,
        file_size_kb=saved.size_kb,
        user_id=current_user.id,
        room_id=room_id,
    )
    db.add(file_upload)
    await db.commit()
    await db.refresh(file_upload)
    return file_upload