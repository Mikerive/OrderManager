from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    # Database
    DATABASE_URL: str = "sqlite:///./orderchainer.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/orderchainer.log"
    
    # Discord
    DISCORD_WEBHOOK_TIMEOUT: int = 5  # seconds

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings()
