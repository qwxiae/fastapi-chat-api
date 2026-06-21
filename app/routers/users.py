from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.core.constants import ALLOWED_IMAGE_TYPES, CACHE_TTL_ACCOUNT
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.file_service import save_avatar
from app.tasks.image_tasks import process_avatar

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
@cache(expire=CACHE_TTL_ACCOUNT)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.username is not None:
        result = await db.execute(
            select(User).where(User.username == payload.username)
        )
        # check if the username already exists
        existing = result.scalar_one_or_none()
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = payload.username

    if payload.bio is not None:
        current_user.bio = payload.bio

    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    saved = await save_avatar(file)
    url = saved.url
    current_user.avatar_url = url
    await db.commit()
    await db.refresh(current_user)

    process_avatar.delay(saved.path)
    
    return current_user