from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base model for user-related operations."""
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=50)

class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    def validate_password(cls, password: str) -> str:
        """
        Validate password strength.
        
        Args:
            password (str): Password to validate
        
        Returns:
            str: Validated password
        
        Raises:
            ValueError: If password does not meet requirements
        """
        # Add more complex password validation if needed
        if not any(char.isdigit() for char in password):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in password):
            raise ValueError('Password must contain at least one uppercase letter')
        return password

class UserResponse(UserBase):
    """Schema for user response, excluding sensitive information."""
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    """Schema for updating user information."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
