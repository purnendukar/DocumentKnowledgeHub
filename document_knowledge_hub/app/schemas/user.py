from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username must contain only letters, numbers, underscores, and hyphens"
    )
    email: EmailStr
    is_active: Optional[bool] = True
    is_superuser: bool = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserInDBBase(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserInDB(UserInDBBase):
    hashed_password: str

    class Config:
        from_attributes = True

class UserInResponse(UserInDBBase):

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass
