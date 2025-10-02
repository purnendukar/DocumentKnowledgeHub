from datetime import timedelta
from json import JSONDecodeError
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ....core.security import create_access_token, get_password_hash, verify_password
from ....core.config import settings
from ....db.session import get_db
from ....schemas.token import Token
from ....schemas.user import UserCreate, UserInDB, UserInResponse
from ....models.user import User as UserModel

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserInResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user.
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


from fastapi import Body

class LoginUser(BaseModel):
    username: str
    password: str

@router.post("/login", response_model=Token)
async def login_access_token(
    form_data: LoginUser = Body(...),
    db: Session = Depends(get_db)
) -> Any:
    """
    JSON body login, returns an access token
    """
    # Look up user
    user = db.execute(
        select(UserModel).where(UserModel.username == form_data.username)
    ).scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Generate token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


