from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from ..auth import get_db, get_current_user
from .. import models, schemas
from ..utils.extractors import extract_text

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.extension import Limiter as SlowLimiter

# Create a limiter instance (memory-based for demo)
limiter = SlowLimiter(key_func=lambda request: request.state.user_key if hasattr(request.state, "user_key") else get_remote_address(request))

router = APIRouter(prefix="/docs", tags=["documents"])

# Helper to set per-user key in request.state, so slowapi can rate-limit per-user
async def set_user_state(request, call_next):
    if "authorization" in request.headers:
        token = request.headers.get("authorization").split(" ")[1]
        # We don't decode here — slowapi key function uses request.state.user_key if set.
        request.state.user_key = token
    return await call_next(request)

@router.post("/upload", response_model=schemas.DocumentOut)
@limiter.limit("100/minute")
async def upload_document(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    # metadata
    filename = file.filename
    size = len(content)
    content_type = file.content_type

    # extract synchronously (could be moved to background)
    extracted_text = extract_text(filename, content)

    doc = models.Document(
        filename=filename,
        size=size,
        content_type=content_type,
        content=extracted_text,
        owner_id=current_user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

@router.get("/search", response_model=List[schemas.DocumentOut])
@limiter.limit("100/minute")
def search_documents(request: Request, q: str = Query(..., min_length=1), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # simple search: keyword in filename or content (case-insensitive)
    pattern = f"%{q}%"
    results = db.query(models.Document).filter(
        (models.Document.owner_id == current_user.id) &
        ((models.Document.filename.ilike(pattern)) | (models.Document.content.ilike(pattern)))
    ).all()
    return results

@router.get("/metadata/{doc_id}", response_model=schemas.DocumentOut)
@limiter.limit("100/minute")
def get_metadata(request: Request, doc_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id, models.Document.owner_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
