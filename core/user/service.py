from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.security import create_access_token
from core.config import settings
from core.decorators import optional_auth
from core.exceptions import UserNotFoundError, DuplicateUserError

from .models import User
from .schemas import UserCreate, UserResponse, UserUpdate, TokenResponse

class UserService:
    """Service for handling user-related operations."""

    def __init__(self, db: Session):
        """Initialize UserService with a database session."""
        self.db = db

    def create_user(self, email: str, password: str, username: str) -> UserResponse:
        """Create a new user."""
        # Validate input
        if not email or "@" not in email or "." not in email:
            raise ValueError("Invalid email format")
        if not username or len(username.strip()) == 0:
            raise ValueError("Username cannot be empty")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")

        # Check if email or username already exists
        existing_user = self.db.query(User).filter(
            (User.email == email) | 
            (User.username == username)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                raise DuplicateUserError(email=email)
            if existing_user.username == username:
                raise DuplicateUserError(username=username)
        
        # Hash the password
        from core.security import get_password_hash
        hashed_password = get_password_hash(password)
        
        # Create user
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Convert SQLAlchemy model to Pydantic model
        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        return UserResponse.model_validate(user_dict)

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError(user_id=user_id)
        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            raise UserNotFoundError(username=username)
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise UserNotFoundError(email=email)
        return user

    def update_user(self, user_id: int, **update_data) -> User:
        """Update user information."""
        user = self.get_user(user_id)
        
        # Check for duplicate email if email is being updated
        if "email" in update_data:
            email = update_data["email"]
            if not email or "@" not in email or "." not in email:
                raise ValueError("Invalid email format")
            
            existing_user = self.db.query(User).filter(
                User.email == email,
                User.id != user_id
            ).first()
            if existing_user:
                raise DuplicateUserError(email=email)
        
        # Validate password if it's being updated
        if "password" in update_data:
            password = update_data["password"]
            if not password or len(password) < 6:
                raise ValueError("Password must be at least 6 characters long")
            from core.security import get_password_hash
            update_data["hashed_password"] = get_password_hash(password)
            del update_data["password"]
        
        # Update user fields
        for key, value in update_data.items():
            setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> None:
        """Delete user."""
        user = self.get_user(user_id)
        self.db.delete(user)
        self.db.commit()

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user."""
        from core.security import verify_password
        
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user

    def create_access_token(self, user: User) -> TokenResponse:
        """Create an access token for a user."""
        # Create access token
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(access_token=access_token)
