from datetime import datetime, timezone
from typing import Optional, Union, List
from pydantic import BaseModel, Field, validator, field_validator


class Token(BaseModel):
    """JWT token response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = "bearer"
    expires_in: int = Field(3600, description="Token expiration time in seconds")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class TokenPayload(BaseModel):
    """JWT token payload model."""
    sub: Union[int, str] = Field(..., description="Subject (user ID)")
    exp: int = Field(..., description="Expiration time (UTC timestamp)")
    iat: int = Field(..., description="Issued at (UTC timestamp)")
    nbf: Optional[int] = Field(None, description="Not before (UTC timestamp)")
    jti: str = Field(..., description="JWT ID")
    type: str = Field("access", description="Token type (access or refresh)")
    scopes: List[str] = Field(default_factory=list, description="List of scopes")

    # @field_validator("exp", "iat", "nbf", mode="before")
    # def convert_timestamps(cls, v):
    #     """Convert timestamps to datetime objects for validation."""
    #     if v is not None and isinstance(v, (int, float)):
    #         return datetime.utcfromtimestamp(v)
    #     return v


class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., min_length=8, max_length=72, description="Password")

    class Config:
        schema_extra = {
            "example": {
                "username": "user@example.com",
                "password": "securepassword123"
            }
        }
