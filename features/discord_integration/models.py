from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import Optional, List

class WebhookConfig(BaseModel):
    """Discord webhook configuration."""
    url: HttpUrl = Field(..., description="Discord webhook URL")
    username: Optional[str] = Field(None, description="Custom username for webhook")
    avatar_url: Optional[HttpUrl] = Field(None, description="Custom avatar URL for webhook")

class NotificationConfig(BaseModel):
    """Configuration for Discord notifications."""
    order_created: bool = Field(True, description="Notify when orders are created")
    order_updated: bool = Field(True, description="Notify when orders are updated")
    order_completed: bool = Field(True, description="Notify when orders are completed")
    order_failed: bool = Field(True, description="Notify when orders fail")

class DiscordIntegrationCreate(BaseModel):
    """Model for creating a new Discord integration."""
    webhook: WebhookConfig
    notifications: NotificationConfig = Field(
        default_factory=NotificationConfig,
        description="Notification preferences"
    )

class DiscordIntegrationUpdate(BaseModel):
    """Model for updating Discord integration settings."""
    webhook: Optional[WebhookConfig] = None
    notifications: Optional[NotificationConfig] = None

class DiscordIntegrationResponse(BaseModel):
    """Model for Discord integration responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    webhook: WebhookConfig
    notifications: NotificationConfig
    is_active: bool = True
