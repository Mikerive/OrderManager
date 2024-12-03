from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_user
from .models import (
    ManagedUser,
    UserRole,
    UserCreate,
    UserUpdate,
    UserProfile,
    TeamCreate,
    TeamUpdate,
    TeamResponse
)
from .service import UserManagementService

router = APIRouter(prefix="/api/user-management", tags=["user-management"])

# User management routes
@router.post("/users/", response_model=UserProfile)
async def create_user(
    user_data: UserCreate,
    current_user: ManagedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    if not current_user.has_permission("manage_users"):
        raise HTTPException(status_code=403, detail="Not authorized to create users")
    
    service = UserManagementService(db)
    return service.create_user(user_data.dict())

@router.put("/users/{user_id}", response_model=UserProfile)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: ManagedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user information (admin or self)."""
    if not current_user.has_permission("manage_users") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    service = UserManagementService(db)
    return service.update_user(user_id, user_data.dict(exclude_unset=True))

@router.get("/users/search", response_model=List[UserProfile])
async def search_users(
    role: Optional[UserRole] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: ManagedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search users with various filters (admin only)."""
    if not current_user.has_permission("manage_users"):
        raise HTTPException(status_code=403, detail="Not authorized to search users")
    
    service = UserManagementService(db)
    return service.search_users(role, department, search, is_active)

@router.get("/users/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: ManagedUser = Depends(get_current_user)
):
    """Get current user's profile."""
    return current_user

@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: int,
    current_user: ManagedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile by ID (admin or self)."""
    if not current_user.has_permission("manage_users") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user")
    
    service = UserManagementService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Team management routes
@router.post("/teams/", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    current_user: ManagedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new team (admin or manager only)."""
    if not current_user.has_permission("manage_teams"):
        raise HTTPException(status_code=403, detail="Not authorized to create teams")
    
    service = UserManagementService(db)
    return service.create_team(team_data.dict())

@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    current_user: ManagedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update team information (admin, manager, or team lead)."""
    service = UserManagementService(db)
    team = service.get_team(team_id)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if not current_user.has_permission("manage_teams") and team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this team")
    
    return service.update_team(team_id, team_data.dict(exclude_unset=True))

@router.post("/teams/{team_id}/members/{user_id}")
async def add_team_member(
    team_id: int,
    user_id: int,
    current_user: ManagedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a user to a team (admin, manager, or team lead)."""
    service = UserManagementService(db)
    team = service.get_team(team_id)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if not current_user.has_permission("manage_teams") and team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify team members")
    
    return service.add_user_to_team(team_id, user_id)

@router.delete("/teams/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: ManagedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a user from a team (admin, manager, or team lead)."""
    service = UserManagementService(db)
    team = service.get_team(team_id)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if not current_user.has_permission("manage_teams") and team.lead_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify team members")
    
    return service.remove_user_from_team(team_id, user_id)

@router.get("/teams/", response_model=List[TeamResponse])
async def list_teams(
    search: Optional[str] = None,
    current_user: ManagedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all teams, optionally filtered by search term."""
    service = UserManagementService(db)
    return service.list_teams(search)

@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    current_user: ManagedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team by ID."""
    service = UserManagementService(db)
    team = service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team
