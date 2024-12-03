from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database.database import get_db
from features.user_management.decorators import require_auth, optional_auth

from .schemas import (
    UserCreate, 
    UserResponse, 
    UserLogin, 
    TokenResponse, 
    UserUpdate
)
from .service import UserService

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        user_data (UserCreate): User registration details
        db (Session): Database session
    
    Returns:
        UserResponse: Created user details
    """
    service = UserService(db)
    return service.create_user(user_data)

@router.post("/login", response_model=TokenResponse)
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and generate an access token.
    
    Args:
        login_data (UserLogin): User login credentials
        db (Session): Database session
    
    Returns:
        TokenResponse: Access token details
    
    Raises:
        HTTPException: If authentication fails
    """
    service = UserService(db)
    user = service.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return service.create_access_token(user)

@router.get("/me", response_model=UserResponse)
@require_auth
def get_current_user(
    db: Session = Depends(get_db),
    current_user: UserResponse = None
):
    """
    Get details of the currently authenticated user.
    
    Args:
        db (Session): Database session
        current_user (UserResponse): Authenticated user
    
    Returns:
        UserResponse: Current user details
    """
    return current_user

@router.put("/me", response_model=UserResponse)
@require_auth
def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = None
):
    """
    Update details of the currently authenticated user.
    
    Args:
        user_update (UserUpdate): User update details
        db (Session): Database session
        current_user (UserResponse): Authenticated user
    
    Returns:
        UserResponse: Updated user details
    """
    service = UserService(db)
    return service.update_user(current_user.id, user_update)
