from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel

class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

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
    log_metadata: Optional[Dict[str, Any]] = None
    created_at: str
    user_id: Optional[int] = None

    class Config:
        from_attributes = True
