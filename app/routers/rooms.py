import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.dependencies import get_current_user, require_room_admin
from app.models.room import Room
from app.models.room_member import RoomMember, RoomRole
from app.models.user import User
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse, RoomMemberResponse
from app.services.file_service import save_avatar

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Room).where(Room.name == payload.name, Room.owner_id == current_user.id))
    obj = result.scalar_one_or_none()

    if obj:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already created a room with this name")
    
    room = Room(
        id=str(uuid.uuid4()),
        name=payload.name,
        description=payload.description,
        is_private=payload.is_private,
        owner_id=current_user.id,
    )
    db.add(room)
    await db.flush()


    member = RoomMember(
        user_id=current_user.id,
        room_id=room.id,
        role=RoomRole.admin,
    )
    db.add(member)
    await db.commit()
    await db.refresh(room)
    return room

@router.get("", response_model=list[RoomResponse])
async def list_rooms(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Room).where(Room.is_private == False))
    return result.scalars().all()


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.is_private:
        member = await db.execute(
            select(RoomMember).where(
                RoomMember.room_id == room_id,
                RoomMember.user_id == current_user.id,
            )
        )
        if not member.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="This room is private")
    return room

@router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: str,
    payload: RoomUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can update this room")

    if payload.name is not None:
        room.name = payload.name
    if payload.description is not None:
        room.description = payload.description
    if payload.is_private is not None:
        room.is_private = payload.is_private

    await db.commit()
    await db.refresh(room)
    return room

@router.post("/{room_id}/avatar", response_model=RoomResponse)
async def upload_room_avatar(
    room_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can set the room avatar")

    result = await save_avatar(file)
    room.avatar_url = result.url
    
    await db.commit()
    await db.refresh(room)
    return room


@router.post("/{room_id}/join", response_model=RoomMemberResponse)
async def join_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.is_private:
        raise HTTPException(status_code=403, detail="This room is private — you need an invite")

    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == current_user.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member")

    member = RoomMember(
        user_id=current_user.id,
        room_id=room_id,
        role=RoomRole.member,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member

@router.delete("/{room_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="You are not a member of this room")

    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if room and room.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Owner cannot leave — transfer ownership or delete the room")

    await db.delete(member)
    await db.commit()


@router.get("/{room_id}/members", response_model=list[RoomMemberResponse])
async def list_members(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    result = await db.execute(
        select(RoomMember).where(RoomMember.room_id == room_id)
    )
    return result.scalars().all()


@router.delete("/{room_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def kick_member(
    room_id: str,
    user_id: str,
    current_user: User = Depends(require_room_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot kick yourself")

    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="User is not a member of this room")

    await db.delete(member)
    await db.commit()