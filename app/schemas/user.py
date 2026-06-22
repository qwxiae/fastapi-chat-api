from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    bio: str | None
    avatar_url: str | None
    created_at: datetime

    # allows reading from sqlalchemy models directly
    # ✅ UserResponse.model_validate(user)
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: str | None = None
    bio: str | None = None
