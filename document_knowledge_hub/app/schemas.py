from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        orm_mode = True

class DocumentCreate(BaseModel):
    filename: str
    size: int
    content_type: Optional[str]

class DocumentOut(BaseModel):
    id: int
    filename: str
    size: int
    content_type: Optional[str]
    uploaded_at: datetime
    owner_id: int

    class Config:
        orm_mode = True
