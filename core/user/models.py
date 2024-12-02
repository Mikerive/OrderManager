from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database.database import Base


class User(Base):
    """
    User model representing registered users in the system.

    Attributes:
        id (int): Unique identifier for the user
        email (str): User's email address (unique)
        username (str): User's username
        hashed_password (str): Hashed password for authentication
        is_active (bool): User account status
        is_superuser (bool): Indicates if user has admin privileges
        created_at (DateTime): Timestamp of user creation
        updated_at (DateTime): Timestamp of last user update

        Relationships:
        - discord_integrations: List of Discord integrations associated with the user
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    discord_integrations = relationship(
        "DiscordIntegration", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        """String representation of the User model."""
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
