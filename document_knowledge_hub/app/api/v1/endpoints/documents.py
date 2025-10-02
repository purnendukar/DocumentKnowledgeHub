from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Request
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from slowapi.extension import Limiter as SlowLimiter

from ....db.session import get_db
from ....models.user import User as UserModel
from ....models.document import Document as DocumentModel
from ....schemas.document import DocumentUpdate, DocumentOut
from ....core.security import get_current_user
from ....utils.extractors import extract_text

# Create a limiter instance (memory-based for demo)
limiter = SlowLimiter(
    key_func=lambda request: request.state.user_id
    if hasattr(request.state, "user_id")
    else get_remote_address(request)
)

router = APIRouter(prefix="/documents", tags=["documents"])


async def set_user_id(request: Request, current_user: UserModel = Depends(get_current_user)):
    """
    Dependency that sets request.state.user_id for the rate limiter.
    """
    request.state.user_id = current_user.id


RATE_LIMIT = "100/minute"

@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMIT)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    _ = Depends(set_user_id)
):
    """
    Upload a new document.
    - **file**: The document file to upload
    - Returns: The created document with metadata
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")

        # Extract metadata
        filename = file.filename
        size = len(content)
        content_type = file.content_type or "application/octet-stream"

        # Extract text content (synchronously for now)
        extracted_text = extract_text(filename, content)

        # Create document record
        doc = DocumentModel(
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

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[DocumentOut])
@limiter.limit(RATE_LIMIT)
async def list_documents(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    _ = Depends(set_user_id)
):
    """
    List all documents for the current user with pagination.
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    return db.query(DocumentModel)\
            .filter(DocumentModel.owner_id == current_user.id)\
            .offset(skip)\
            .limit(limit)\
            .all()

@router.get("/search", response_model=List[DocumentOut])
@limiter.limit(RATE_LIMIT)
async def search_documents(
    request: Request,
    q: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    _ = Depends(set_user_id)
):
    """
    Search documents by content or filename.
    - **q**: Search query string
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    pattern = f"%{q}%"
    return db.query(DocumentModel)\
            .filter(
                (DocumentModel.owner_id == current_user.id) &
                ((DocumentModel.filename.ilike(pattern)) | 
                 (DocumentModel.content.ilike(pattern)))
            )\
            .offset(skip)\
            .limit(limit)\
            .all()

@router.get("/{document_id}", response_model=DocumentOut)
@limiter.limit(RATE_LIMIT)
async def get_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    _ = Depends(set_user_id)
):
    """
    Get document by ID.
    - **document_id**: ID of the document to retrieve
    """
    doc = db.query(DocumentModel)\
            .filter(
                DocumentModel.id == document_id,
                DocumentModel.owner_id == current_user.id
            )\
            .first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.put("/{document_id}", response_model=DocumentOut)
@limiter.limit(RATE_LIMIT)
async def update_document(
    request: Request,
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    _ = Depends(set_user_id)
):
    """
    Update document metadata.
    - **document_id**: ID of the document to update
    - **document_update**: Fields to update
    """
    doc = db.query(DocumentModel)\
            .filter(
                DocumentModel.id == document_id,
                DocumentModel.owner_id == current_user.id
            )\
            .first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update fields
    for field, value in document_update.dict(exclude_unset=True).items():
        setattr(doc, field, value)
    
    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return doc

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(RATE_LIMIT)
async def delete_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    _ = Depends(set_user_id)
):
    """
    Delete a document.
    - **document_id**: ID of the document to delete
    """
    doc = db.query(DocumentModel)\
            .filter(
                DocumentModel.id == document_id,
                DocumentModel.owner_id == current_user.id
            )\
            .first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(doc)
    db.commit()
    return None
