import pytest
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import jwt

from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings

def test_register_user(client, test_user, db_session):
    # Test successful user registration
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": test_user["username"],
            "email": test_user["email"],
            "password": test_user["password"]
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    # Handle different possible response formats
    user_data = data.get('user', data)
    assert user_data["username"] == test_user["username"]
    assert user_data["email"] == test_user["email"]
    assert "id" in user_data
    assert "hashed_password" not in user_data

def test_register_existing_user(client, test_user, db_session):
    # Test registering with an existing username
    # First create a user
    db_user = User(
        username=test_user["username"],
        email=test_user["email"],
        hashed_password=get_password_hash(test_user["password"])
    )
    db_session.add(db_user)
    db_session.commit()
    
    # Try to register with same username
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": test_user["username"],
            "email": "newemail@example.com",
            "password": "newpassword"
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already registered" in response.text

def test_login_success(client, test_user, db_session):
    # Create a test user
    db_user = User(
        username=test_user["username"],
        email=test_user["email"],
        hashed_password=get_password_hash(test_user["password"])
    )
    db_session.add(db_user)
    db_session.commit()
    
    # Test successful login - try both possible endpoints
    response = client.post(
        "/api/v1/auth/login",
        json={  # Using form data for token endpoint
            "username": test_user["username"],
            "password": test_user["password"]
        },
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Handle different possible token response formats
    token = data.get('access_token') or data.get('token')
    token_type = data.get('token_type', '').lower()
    
    assert token is not None
    assert token_type == 'bearer'
    
    # Verify the token is valid
    payload = jwt.decode(
        token,
        key=settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    assert "sub" in payload
    assert payload["sub"] == str(db_user.id)

def test_login_invalid_credentials(client, test_user, db_session):
    # Create a test user
    db_user = User(
        username=test_user["username"],
        email=test_user["email"],
        hashed_password=get_password_hash(test_user["password"])
    )
    db_session.add(db_user)
    db_session.commit()
    
    # Test login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user["username"],
            "password": "wrongpassword"
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Incorrect username or password" in response.text
