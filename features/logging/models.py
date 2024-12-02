from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# SQLAlchemy Model
class LogEntry(Base):
    """Log entry database model."""
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String)
    message = Column(String)
    source = Column(String)
    log_metadata = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationship
    user = relationship("User", backref="log_entries")

# Pydantic Schemas
class LogCreate(BaseModel):
    """Schema for creating a log entry."""
    level: LogLevel
    message: str
    source: str
    metadata: Optional[Dict[str, Any]] = None

class LogResponse(BaseModel):
    """Schema for log entry response."""
    id: int
    level: LogLevel
    message: str
    source: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    user_id: Optional[int] = None

    class Config:
        orm_mode = True
