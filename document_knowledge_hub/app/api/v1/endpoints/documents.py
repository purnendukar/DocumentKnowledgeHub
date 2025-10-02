import os
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Request, Query, Path, \
    Body
from pydantic import BaseModel, Field
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from slowapi.extension import Limiter as SlowLimiter
from dotenv import load_dotenv

from ....db.session import get_db
from ....models.user import User as UserModel
from ....models.document import Document as DocumentModel
from ....schemas.document import DocumentUpdate, DocumentOut
from ....core.security import get_current_user
from ....utils.extractors import extract_text



load_dotenv()
RATE_LIMIT_PER_MINUTE = os.getenv("RATE_LIMIT_PER_MINUTE", 100)
RATE_LIMIT = f"{RATE_LIMIT_PER_MINUTE}/minute"

# Request/Response Models for API documentation
class DocumentCreate(BaseModel):
    """Document creation model with file upload."""
    file: UploadFile = Field(..., description="Document file to upload (PDF, DOCX, or TXT)")
    
    class Config:
        schema_extra = {
            "example": {
                "file": "example.pdf"
            }
        }

class DocumentResponse(DocumentOut):
    """Document response model with additional metadata."""
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "filename": "example.pdf",
                "content_type": "application/pdf",
                "size": 1024,
                "uploaded_at": "2023-01-01T12:00:00Z",
                "content": "Extracted text content from the document..."
            }
        }

class DocumentListResponse(BaseModel):
    """Paginated list of documents."""
    items: List[DocumentOut] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    skip: int = Field(..., description="Number of documents skipped")
    limit: int = Field(..., description="Maximum number of documents returned")
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "filename": "example.pdf",
                        "content_type": "application/pdf",
                        "size": 1024,
                        "uploaded_at": "2023-01-01T12:00:00Z"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 10
            }
        }

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

@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Document uploaded successfully"},
        400: {"description": "Invalid file type or content"},
        401: {"description": "Not authenticated"},
        413: {"description": "File too large"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)
@limiter.limit(RATE_LIMIT)
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="Document file to upload (PDF, DOCX, or TXT)"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    _ = Depends(set_user_id)
):
    """
    Upload a new document to the knowledge hub.
    
    ### Supported File Types:
    - PDF (.pdf)
    - Word (.docx)
    - Text (.txt)
    
    ### File Size Limit:
    - Maximum 10MB per file
    
    ### Authentication:
    - Requires valid JWT token in Authorization header
    
    ### Rate Limit:
    - 100 requests per minute per user
    
    ### Returns:
    - Document metadata and extracted text content
    """
    # Validate file type first before reading content
    allowed_content_types = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    }

    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Supported types: {', '.join(allowed_content_types)}"
        )

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

@router.get(
    "",
    response_model=DocumentListResponse,
    responses={
        200: {"description": "List of documents retrieved successfully"},
        401: {"description": "Not authenticated"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit(RATE_LIMIT)
async def list_documents(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    _ = Depends(set_user_id)
):
    """
    List all documents for the current user with pagination.
    
    ### Query Parameters:
    - **skip**: Number of documents to skip (default: 0)
    - **limit**: Maximum number of documents to return (default: 10, max: 100)
    
    ### Authentication:
    - Requires valid JWT token in Authorization header
    
    ### Rate Limit:
    - 100 requests per minute per user
    
    ### Returns:
    - Paginated list of document metadata
    """
    return db.query(DocumentModel)\
            .filter(DocumentModel.owner_id == current_user.id)\
            .offset(skip)\
            .limit(limit)\
            .all()

@router.get(
    "/search",
    response_model=DocumentListResponse,
    responses={
        200: {"description": "Search results retrieved successfully"},
        400: {"description": "Invalid search query"},
        401: {"description": "Not authenticated"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit(RATE_LIMIT)
async def search_documents(
    request: Request,
    q: str = Query(..., min_length=2, max_length=100, description="Search query string"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    _ = Depends(set_user_id)
):
    """
    Search documents by content or filename.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    try:
        pattern = f"%{q}%"

        # Get total count first
        total = db.query(DocumentModel) \
            .filter(
            (DocumentModel.owner_id == current_user.id) &
            ((DocumentModel.filename.ilike(pattern)) |
             (DocumentModel.content.ilike(pattern)))
        ).count()

        # Get paginated results
        results: List[DocumentModel] = db.query(DocumentModel) \
            .filter(
            (DocumentModel.owner_id == current_user.id) &
            ((DocumentModel.filename.ilike(pattern)) |
             (DocumentModel.content.ilike(pattern)))
        ).offset(skip).limit(limit).all()

        return DocumentListResponse(
            items=[DocumentOut.model_validate(doc) for doc in results],
            total=total,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    responses={
        200: {"description": "Document retrieved successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to access this document"},
        404: {"description": "Document not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit(RATE_LIMIT)
async def get_document(
    request: Request,
    document_id: int = Path(..., description="ID of the document to retrieve", example=1),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    _ = Depends(set_user_id)
):
    """
    Retrieve a document by its ID.
    
    ### Path Parameters:
    - **document_id**: The unique identifier of the document
    
    ### Authentication:
    - Requires valid JWT token in Authorization header
    - User must be the owner of the document
    
    ### Rate Limit:
    - 100 requests per minute per user
    
    ### Returns:
    - Complete document metadata and content
    
    ### Errors:
    - 403: If user is not the owner of the document
    - 404: If document with the specified ID is not found
    """
    doc = db.query(DocumentModel)\
            .filter(
                DocumentModel.id == document_id
            )\
            .first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.owner_id!=current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")

    return doc

@router.put(
    "/{document_id}",
    response_model=DocumentResponse,
    responses={
        200: {"description": "Document updated successfully"},
        400: {"description": "Invalid update data"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to update this document"},
        404: {"description": "Document not found"},
        409: {"description": "Document with this name already exists"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit(RATE_LIMIT)
async def update_document(
    request: Request,
    document_id: int = Path(..., description="ID of the document to update", example=1),
    document_update: DocumentUpdate = Body(..., description="Document fields to update"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    _ = Depends(set_user_id)
):
    """
    Update document metadata.
    
    ### Path Parameters:
    - **document_id**: The unique identifier of the document to update
    
    ### Request Body:
    - **filename** (optional): New filename for the document
    - **content** (optional): Updated text content for the document
    
    ### Authentication:
    - Requires valid JWT token in Authorization header
    - User must be the owner of the document
    
    ### Rate Limit:
    - 100 requests per minute per user
    
    ### Returns:
    - Updated document with all metadata
    
    ### Errors:
    - 400: If update data is invalid
    - 403: If user is not the owner of the document
    - 404: If document with the specified ID is not found
    - 409: If a document with the new filename already exists
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

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Document deleted successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to delete this document"},
        404: {"description": "Document not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit(RATE_LIMIT)
async def delete_document(
    request: Request,
    document_id: int = Path(..., description="ID of the document to delete", example=1),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    _ = Depends(set_user_id)
):
    """
    Delete a document by its ID.
    
    ### Path Parameters:
    - **document_id**: The unique identifier of the document to delete
    
    ### Authentication:
    - Requires valid JWT token in Authorization header
    - User must be the owner of the document
    
    ### Rate Limit:
    - 100 requests per minute per user
    
    ### Returns:
    - 204 No Content on successful deletion
    
    ### Errors:
    - 403: If user is not the owner of the document
    - 404: If document with the specified ID is not found
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
