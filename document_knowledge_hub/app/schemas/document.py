from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class DocumentBase(BaseModel):
    filename: str
    content_type: Optional[str] = None
    size: Optional[int] = None

class DocumentCreate(DocumentBase):
    content: str

class DocumentUpdate(BaseModel):
    filename: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None

class DocumentInDBBase(DocumentBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True

class Document(DocumentInDBBase):
    content: Optional[str] = None

class DocumentOut(DocumentInDBBase):
    pass
