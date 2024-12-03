from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

class WebhookConfig(BaseModel):
    """Discord webhook configuration."""
    url: HttpUrl
    username: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None

class NotificationConfig(BaseModel):
    """Notification configuration for Discord integration."""
    order_created: bool = False
    order_updated: bool = False
    order_completed: bool = False
    order_failed: bool = False

class DiscordIntegrationCreate(BaseModel):
    """Schema for creating a Discord integration."""
    webhook: WebhookConfig
    notifications: NotificationConfig

class DiscordIntegrationUpdate(BaseModel):
    """Schema for updating a Discord integration."""
    webhook: Optional[WebhookConfig] = None
    notifications: Optional[NotificationConfig] = None

class DiscordIntegrationResponse(BaseModel):
    """Response schema for Discord integration."""
    id: int
    user_id: int
    webhook: WebhookConfig
    notifications: NotificationConfig
    is_active: bool = True


from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from core.database.database import Base
from core.user.models import User

class DiscordIntegration(Base):
    """
    Model representing Discord webhook integration for a user.
    
    Attributes:
        id (int): Unique identifier for the integration
        user_id (int): Foreign key to the User model
        webhook_url (str): Discord webhook URL
        webhook_username (str, optional): Custom username for webhook
        webhook_avatar_url (str, optional): Custom avatar URL for webhook
        notify_order_created (bool): Flag for order creation notifications
        notify_order_updated (bool): Flag for order update notifications
        notify_order_completed (bool): Flag for order completion notifications
        notify_order_failed (bool): Flag for order failure notifications
        
        Relationships:
        - user: Associated User model
    """
    __tablename__ = "discord_integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    webhook_url = Column(String, nullable=False)
    webhook_username = Column(String, nullable=True)
    webhook_avatar_url = Column(String, nullable=True)
    
    notify_order_created = Column(Boolean, default=False)
    notify_order_updated = Column(Boolean, default=False)
    notify_order_completed = Column(Boolean, default=False)
    notify_order_failed = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="discord_integrations")

    def __repr__(self):
        """String representation of the DiscordIntegration model."""
        return f"<DiscordIntegration(id={self.id}, user_id={self.user_id}, webhook_url='{self.webhook_url}')>"
