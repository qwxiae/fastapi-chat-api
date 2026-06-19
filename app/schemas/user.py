from pydantic import BaseModel, EmailStr
from datetime import datetime

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