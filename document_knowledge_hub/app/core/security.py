import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Dict, Any

from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..core.config import settings
from ..db.session import get_db
from ..models.user import User as UserModel
from ..schemas.token import TokenPayload

# HTTP Bearer token scheme
security = HTTPBearer()

# Password hashing with bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=14  # Increased from default 12 for better security
)

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days for refresh tokens

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Log the error in production
        print(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    # Ensure password is a string and not too long for bcrypt (72 bytes max)
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
    
    # Convert to bytes and check length
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:  # bcrypt's max length
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    
    return pwd_context.hash(password)

def create_jwt_token(
    subject: Union[str, int],
    token_type: str = TOKEN_TYPE_ACCESS,
    expires_delta: Optional[timedelta] = None,
    scopes: list[str] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT token (access or refresh).
    
    Args:
        subject: The subject of the token (usually user ID)
        token_type: Type of token ('access' or 'refresh')
        expires_delta: Optional timedelta for token expiration
        scopes: List of scopes the token has access to
        additional_claims: Additional claims to include in the token
        
    Returns:
        str: Encoded JWT token
    """
    if token_type not in [TOKEN_TYPE_ACCESS, TOKEN_TYPE_REFRESH]:
        raise ValueError(f"Invalid token type: {token_type}")
        
    if token_type == TOKEN_TYPE_ACCESS and not expires_delta:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    elif token_type == TOKEN_TYPE_REFRESH and not expires_delta:
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    
    # Standard claims (https://datatracker.ietf.org/doc/html/rfc7519#section-4.1)
    to_encode = {
        "sub": str(subject),  # Subject (user ID)
        "iat": int(now.timestamp()),  # Issued At (as timestamp)
        "exp": int(expire.timestamp()),  # Expiration Time (as timestamp)
        "nbf": int(now.timestamp()),  # Not Before (as timestamp)
        "jti": str(uuid.uuid4()),  # JWT ID
        "type": token_type,
        "scopes": scopes or []
    }
    
    # Add additional claims if provided
    if additional_claims:
        to_encode.update(additional_claims)
    
    # Encode the token with the secret key
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    return encoded_jwt


def create_access_token(
    user_id: Union[str, int],
    scopes: list[str] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create an access token for a user.
    
    Args:
        user_id: The ID of the user
        scopes: List of scopes the token should have
        additional_claims: Additional claims to include in the token
        
    Returns:
        str: Encoded JWT access token
    """
    return create_jwt_token(
        subject=user_id,
        token_type=TOKEN_TYPE_ACCESS,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        scopes=scopes,
        additional_claims=additional_claims
    )


def create_refresh_token(
    user_id: Union[str, int],
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a refresh token for a user.
    
    Args:
        user_id: The ID of the user
        additional_claims: Additional claims to include in the token
        
    Returns:
        str: Encoded JWT refresh token
    """
    return create_jwt_token(
        subject=user_id,
        token_type=TOKEN_TYPE_REFRESH,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        additional_claims=additional_claims
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Get the current authenticated user from the JWT token.
    
    This is a dependency that can be used in FastAPI path operations to get the
    current user. It validates the JWT token and checks if the user exists.
    
    Args:
        credentials: HTTP Authorization credentials containing the JWT token
        db: Database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If the token is invalid, expired, or the user doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "verify_signature": True,
                "verify_aud": False,
                "verify_iss": False,
                "verify_iat": True,
                "verify_exp": True,
                "verify_nbf": False,
                "verify_sub": True,
                "verify_jti": True,
            }
        )
        print(payload)
        
        # Validate required claims
        token_data = TokenPayload(**payload)
        
        # Get user ID from token
        user_id = token_data.sub
        if user_id is None:
            raise credentials_exception
            
    except (JWTError, ValidationError) as e:
        print(e)
        if isinstance(e, ExpiredSignatureError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"The access token expired\""},
            )
        raise credentials_exception
    
    # Get user from database
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        The decoded token payload if valid, None otherwise
        
    Raises:
        JWTError: If the token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "verify_signature": True,
                "verify_aud": False,
                "verify_iat": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iss": True,
                "verify_sub": True,
                "verify_jti": True,
            }
        )
        return payload
    except JWTError as e:
        # Log the error for debugging
        print(f"Token verification failed: {e}")
        raise


async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Dependency to get the current active user.
    
    This is a simpler version of get_current_user that can be used when you just
    need to check if the user is authenticated.
    """
    return current_user


async def get_current_active_admin(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Dependency to get the current active admin user.
    
    This checks if the user is an admin.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user
