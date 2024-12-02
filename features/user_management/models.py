from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Boolean, Column, String, DateTime, Table, ForeignKey, Integer
from sqlalchemy.orm import relationship
import enum

from core.user.model import User as BaseUser
from core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    TEAM_LEAD = "team_lead"
    MEMBER = "member"
    GUEST = "guest"

# Association table for user teams
user_teams = Table(
    'user_teams',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('team_id', Integer, ForeignKey('teams.id'), primary_key=True)
)

class Team(Base):
    """Team model for organizing users."""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = relationship("ManagedUser", secondary=user_teams, backref="teams")
    lead_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    team_lead = relationship("ManagedUser", foreign_keys=[lead_id])

class ManagedUser(BaseUser):
    """
    Extended User model with management features like roles and teams.
    """
    __tablename__ = None  # Extends the base users table

    # Additional columns for user management
    role = Column(String, default=UserRole.MEMBER)
    is_superuser = Column(Boolean, default=False)
    department = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission based on role."""
        role_permissions = {
            UserRole.ADMIN: ["all"],
            UserRole.MANAGER: ["manage_users", "manage_teams", "manage_orders"],
            UserRole.TEAM_LEAD: ["manage_team_orders", "view_team_stats"],
            UserRole.MEMBER: ["create_orders", "view_own_orders"],
            UserRole.GUEST: ["view_own_orders"]
        }
        
        if self.is_superuser:
            return True
            
        user_permissions = role_permissions.get(self.role, [])
        return "all" in user_permissions or permission in user_permissions

# Pydantic models for API
class TeamBase(BaseModel):
    """Base model for Team data."""
    name: str
    description: Optional[str] = None

class TeamCreate(TeamBase):
    """Model for creating a team."""
    lead_id: Optional[int] = None

class TeamUpdate(TeamBase):
    """Model for updating a team."""
    name: Optional[str] = None
    lead_id: Optional[int] = None

class TeamResponse(TeamBase):
    """Model for team responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    lead_id: Optional[int]
    member_count: int

    class Config:
        orm_mode = True

class UserProfile(BaseModel):
    """Extended user profile information."""
    email: EmailStr
    username: Optional[str] = None
    role: UserRole
    department: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    teams: List[TeamResponse] = []

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    """Model for creating a user."""
    email: EmailStr
    username: Optional[str] = None
    password: str
    role: UserRole = Field(UserRole.MEMBER, description="User's role in the system")
    department: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None

class UserUpdate(BaseModel):
    """Model for updating a user."""
    username: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
