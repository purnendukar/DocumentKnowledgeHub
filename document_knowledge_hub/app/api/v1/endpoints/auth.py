from datetime import timedelta
from json import JSONDecodeError
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from ....core.security import create_access_token, get_password_hash, verify_password
from ....db.session import get_db
from ....schemas.token import Token
from ....schemas.user import UserCreate, UserInDB, UserInResponse
from ....models.user import User as UserModel

# Request/Response Models for API documentation
class TokenResponse(Token):
    """Token response model with additional user information."""
    token_type: str = Field(..., example="bearer")
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

class UserRegisterRequest(UserCreate):
    """User registration request model with validation examples."""
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "johndoe@example.com",
                "password": "securepassword123"
            }
        }

class UserLoginRequest(BaseModel):
    """User login request model with validation examples."""
    username: str = Field(..., example="johndoe")
    password: str = Field(..., example="securepassword123")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "securepassword123"
            }
        }

class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str = Field(..., example="Error message describing the issue")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Error message describing the issue"
            }
        }

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post(
    "/register",
    response_model=UserInResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User registered successfully"},
        400: {"model": ErrorResponse, "description": "Username or email already registered"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
async def register_user(
    user_in: UserRegisterRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user in the system.
    
    - **username**: Must be unique (3-50 characters, alphanumeric + underscore)
    - **email**: Must be a valid email address
    - **password**: Must be at least 8 characters long
    
    Returns the created user object (password hash is not included).
    """
    # Check if username already exists
    db_user = db.query(UserModel).filter(UserModel.username == user_in.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_email = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_in.password)
    db_user = UserModel(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserInResponse(user=UserInDB.from_attributes(db_user))


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        200: {"description": "Successfully authenticated"},
        400: {"model": ErrorResponse, "description": "Incorrect username or password"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
async def login_access_token(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    - **username**: The user's username
    - **password**: The user's password
    
    Returns an access token that should be included in the Authorization header
    for subsequent requests as: `Authorization: Bearer <token>`
    
    The token expires after the time specified in `ACCESS_TOKEN_EXPIRE_MINUTES`.
    """
    # Check if user exists and password is correct
    user = db.execute(
        select(UserModel).where(UserModel.username == request.username)
    ).scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token = create_access_token(
        user_id=user.id
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        }
    }


