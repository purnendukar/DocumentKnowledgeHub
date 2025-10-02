import os
import tempfile
import pytest
from fastapi import status
from app.models.user import User
from app.core.security import get_password_hash
from tests.utils.auth import get_auth_headers

def create_test_file(content, extension=".txt"):
    """Helper function to create a test file with given content and extension."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
    temp_file.write(content.encode())
    temp_file.close()
    return temp_file.name

# Test text file upload
def test_upload_text_file(client, test_user, db_session):
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
    
    # Create a test text file
    test_content = "This is a test text file content."
    test_file = create_test_file(test_content, ".txt")
    
    try:
        # Upload the file
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
        assert data["size"] == len(test_content)
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)

# Test PDF file upload
@pytest.mark.skip(reason="Requires PyPDF2 to be properly installed in test environment")
def test_upload_pdf_file(client, test_user, db_session):
    # Create a test user
    db_user = User(
        username=test_user["username"],
        email=test_user["email"],
        hashed_password=get_password_hash(test_user["password"])
    )
    db_session.add(db_user)
    db_session.commit()
    
    # Login to get token
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Create a simple PDF file (this is a minimal valid PDF)
    pdf_content = """%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << >> /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 24 Tf 100 700 Td (Hello, World!) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000109 00000 n 
0000000184 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
234
%%EOF"""
    
    test_file = create_test_file(pdf_content, ".pdf")
    
    try:
        # Upload the file
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/v1/documents",
                files={"file": ("test.pdf", f, "application/pdf")},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["content_type"] == "application/pdf"
        assert data["size"] > 0
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)

# Test invalid file type
def test_upload_invalid_file_type(client, test_user, db_session):
    # Create a test user
    db_user = User(
        username=test_user["username"],
        email=test_user["email"],
        hashed_password=get_password_hash(test_user["password"])
    )
    db_session.add(db_user)
    db_session.commit()
    
    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": test_user["username"], "password": test_user["password"]}
    )
    print("login_response", login_response.json())
    token = login_response.json()["access_token"]
    
    # Create a test file with invalid extension
    test_content = "This is a test file with invalid extension."
    test_file = create_test_file(test_content, ".invalid")
    
    try:
        # Try to upload the file
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/v1/documents",
                files={"file": ("test.invalid", f, "application/octet-stream")},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        # Should return 400 Bad Request for unsupported file type
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported file type" in response.text
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)
