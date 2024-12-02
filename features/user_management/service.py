from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException

from .models import (
    ManagedUser,
    Team,
    UserRole,
    user_teams
)
from core.auth import get_password_hash

class UserManagementService:
    """Service for managing users and teams."""

    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_data: dict) -> ManagedUser:
        """Create a new managed user."""
        # Check if email already exists
        if self.db.query(ManagedUser).filter(ManagedUser.email == user_data["email"]).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash the password
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        
        user = ManagedUser(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user_id: int, user_data: dict) -> ManagedUser:
        """Update user information."""
        user = self.db.query(ManagedUser).filter(ManagedUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        for key, value in user_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int) -> Optional[ManagedUser]:
        """Get user by ID."""
        return self.db.query(ManagedUser).filter(ManagedUser.id == user_id).first()

    def search_users(
        self,
        role: Optional[UserRole] = None,
        department: Optional[str] = None,
        search_term: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[ManagedUser]:
        """Search users with various filters."""
        query = self.db.query(ManagedUser)

        if role:
            query = query.filter(ManagedUser.role == role)
        if department:
            query = query.filter(ManagedUser.department == department)
        if is_active is not None:
            query = query.filter(ManagedUser.is_active == is_active)
        if search_term:
            search_filter = or_(
                ManagedUser.email.ilike(f"%{search_term}%"),
                ManagedUser.username.ilike(f"%{search_term}%")
            )
            query = query.filter(search_filter)

        return query.all()

    # Team management
    def create_team(self, team_data: dict) -> Team:
        """Create a new team."""
        if self.db.query(Team).filter(Team.name == team_data["name"]).first():
            raise HTTPException(status_code=400, detail="Team name already exists")

        team = Team(**team_data)
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def update_team(self, team_id: int, team_data: dict) -> Team:
        """Update team information."""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if "name" in team_data and team_data["name"] != team.name:
            if self.db.query(Team).filter(Team.name == team_data["name"]).first():
                raise HTTPException(status_code=400, detail="Team name already exists")

        for key, value in team_data.items():
            if hasattr(team, key) and value is not None:
                setattr(team, key, value)

        self.db.commit()
        self.db.refresh(team)
        return team

    def add_user_to_team(self, team_id: int, user_id: int) -> Team:
        """Add a user to a team."""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        user = self.db.query(ManagedUser).filter(ManagedUser.id == user_id).first()

        if not team or not user:
            raise HTTPException(status_code=404, detail="Team or user not found")

        if user not in team.members:
            team.members.append(user)
            self.db.commit()
            self.db.refresh(team)

        return team

    def remove_user_from_team(self, team_id: int, user_id: int) -> Team:
        """Remove a user from a team."""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        user = self.db.query(ManagedUser).filter(ManagedUser.id == user_id).first()

        if not team or not user:
            raise HTTPException(status_code=404, detail="Team or user not found")

        if user in team.members:
            team.members.remove(user)
            self.db.commit()
            self.db.refresh(team)

        return team

    def get_team(self, team_id: int) -> Optional[Team]:
        """Get team by ID."""
        return self.db.query(Team).filter(Team.id == team_id).first()

    def list_teams(self, search_term: Optional[str] = None) -> List[Team]:
        """List all teams, optionally filtered by search term."""
        query = self.db.query(Team)
        
        if search_term:
            query = query.filter(
                or_(
                    Team.name.ilike(f"%{search_term}%"),
                    Team.description.ilike(f"%{search_term}%")
                )
            )
        
        return query.all()

    def get_user_teams(self, user_id: int) -> List[Team]:
        """Get all teams a user belongs to."""
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user.teams
