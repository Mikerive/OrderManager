from functools import wraps
from typing import Callable, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from core.config import settings
from core.database.database import get_db
from features.user_management.models import User
from features.user_management.auth import oauth2_scheme

def authenticate_user(db: Session, token: str):
    """
    Authenticate a user based on JWT token.
    
    Args:
        db (Session): Database session
        token (str): JWT token
    
    Returns:
        User: Authenticated user
    
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        # Try to get email or user ID
        email_or_id = payload.get("sub")
        if email_or_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Try to find user by email or ID
    user = (
        db.query(User)
        .filter(
            (User.email == email_or_id) | (User.id == int(email_or_id))
        )
        .first()
    )
    
    if user is None:
        raise credentials_exception
    
    return user

def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for a route.
    
    This decorator can be used on route handlers to ensure 
    the user is authenticated before accessing the route.
    
    Args:
        func (Callable): The route handler function
    
    Returns:
        Callable: Wrapped route handler with authentication
    """
    @wraps(func)
    async def wrapper(*args, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), **kwargs):
        # Authenticate the user
        user = authenticate_user(db, token)
        
        # Add the authenticated user to the kwargs
        kwargs['current_user'] = user
        
        # Call the original function
        return await func(*args, **kwargs)
    
    return wrapper

def optional_auth(func: Callable) -> Callable:
    """
    Decorator to optionally authenticate a user.
    
    This decorator attempts to authenticate the user but 
    does not require authentication. If authentication fails, 
    current_user will be None.
    
    Args:
        func (Callable): The route handler function
    
    Returns:
        Callable: Wrapped route handler with optional authentication
    """
    @wraps(func)
    async def wrapper(*args, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), **kwargs):
        try:
            # Try to authenticate the user
            user = authenticate_user(db, token)
            kwargs['current_user'] = user
        except HTTPException:
            # If authentication fails, set current_user to None
            kwargs['current_user'] = None
        
        # Call the original function
        return await func(*args, **kwargs)
    
    return wrapper
