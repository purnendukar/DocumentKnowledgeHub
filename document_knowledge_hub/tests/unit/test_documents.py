from fastapi import status
from app.models.user import User
from app.models.document import Document
from app.core.security import get_password_hash
from tests.utils.auth import get_auth_headers

# Test document upload
def test_upload_document(client, test_user, db_session, test_file):
    # Create a test user
    db_user = User(
        username=test_user["username"],
        email=test_user["email"],
        hashed_password=get_password_hash(test_user["password"])
    )
    db_session.add(db_user)
    db_session.commit()
    
    # Get auth headers
    headers = get_auth_headers(client, test_user["username"], test_user["password"])
    
    # Upload a file
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/documents",
            files={"file": ("test.txt", f, "text/plain")},
            headers=headers
        )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["content_type"] == "text/plain"
    assert data["size"] > 0

# Test document retrieval
def test_get_document(client, test_user, db_session):
    # Create a test user and document
    db_user = User(
        username=test_user["username"],
        email=test_user["email"],
        hashed_password=get_password_hash(test_user["password"])
    )
    db_session.add(db_user)
    db_session.commit()
    
    test_doc = Document(
        filename="test.txt",
        content_type="text/plain",
        size=100,
        content="Test content",
        owner_id=db_user.id
    )
    db_session.add(test_doc)
    db_session.commit()
    
    # Get auth headers
    headers = get_auth_headers(client, test_user["username"], test_user["password"])
    
    # Get the document
    response = client.get(
        f"/api/v1/documents/{test_doc.id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_doc.id
    assert data["filename"] == "test.txt"

# Test document search
def test_search_documents(client, test_user, db_session):
    # Create a test user and documents
    db_user = User(
        username=test_user["username"],
        email=test_user["email"],
        hashed_password=get_password_hash(test_user["password"])
    )
    db_session.add(db_user)
    db_session.commit()
    
    # Add test documents
    docs = [
        {"filename": "doc1.txt", "content": "This is a test document about Python"},
        {"filename": "doc2.txt", "content": "Another document about testing"},
        {"filename": "doc3.txt", "content": "Document about FastAPI"}
    ]
    
    for doc in docs:
        db_doc = Document(
            filename=doc["filename"],
            content_type="text/plain",
            size=len(doc["content"]),
            content=doc["content"],
            owner_id=db_user.id
        )
        db_session.add(db_doc)
    
    db_session.commit()
    
    # Get auth headers
    headers = get_auth_headers(client, test_user["username"], test_user["password"])
    
    # Search for documents
    response = client.get(
        "/api/v1/documents/search",
        params={"q": "Python"},
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    items = response.json()["items"]
    assert len(items) == 1

# Test unauthorized access
def test_unauthorized_access(client):
    # Try to access protected route without token
    response = client.get("/api/v1/documents/1")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Try with invalid token
    response = client.get(
        "/api/v1/documents/1",
        headers={"Authorization": "Bearer invalidtoken123"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
