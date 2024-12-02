from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from core.auth import get_current_user
from core.models import User
from .models import (
    DiscordIntegrationCreate,
    DiscordIntegrationUpdate,
    DiscordIntegrationResponse,
    WebhookConfig,
    NotificationConfig
)
from .service import DiscordService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/discord", tags=["discord"])

@router.post("/", response_model=DiscordIntegrationResponse)
async def create_discord_integration(
    integration: DiscordIntegrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new Discord integration."""
    logger.info(f"CREATE DISCORD INTEGRATION ROUTE CALLED by user {current_user.email}")
    logger.debug(f"Integration details: {integration}")
    
    # Create integration
    db_integration = await DiscordService.create_integration(db, integration, current_user)
    
    # Convert to response model
    return DiscordIntegrationResponse(
        id=db_integration.id,
        user_id=db_integration.user_id,
        webhook=WebhookConfig(
            url=db_integration.webhook_url,
            username=db_integration.webhook_username,
            avatar_url=db_integration.webhook_avatar_url
        ),
        notifications=NotificationConfig(
            order_created=db_integration.notify_order_created,
            order_updated=db_integration.notify_order_updated,
            order_completed=db_integration.notify_order_completed,
            order_failed=db_integration.notify_order_failed
        ),
        is_active=True
    )

@router.get("/", response_model=DiscordIntegrationResponse)
async def get_discord_integration(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Discord integration for the current user."""
    logger.info(f"GET DISCORD INTEGRATION ROUTE CALLED by user {current_user.email}")
    
    # Get integration
    db_integration = await DiscordService.get_integration(db, current_user)
    
    # Check if integration exists
    if not db_integration:
        logger.warning(f"No Discord integration found for user {current_user.email}")
        raise HTTPException(
            status_code=404,
            detail="Discord integration not found"
        )
    
    # Convert to response model
    return DiscordIntegrationResponse(
        id=db_integration.id,
        user_id=db_integration.user_id,
        webhook=WebhookConfig(
            url=db_integration.webhook_url,
            username=db_integration.webhook_username,
            avatar_url=db_integration.webhook_avatar_url
        ),
        notifications=NotificationConfig(
            order_created=db_integration.notify_order_created,
            order_updated=db_integration.notify_order_updated,
            order_completed=db_integration.notify_order_completed,
            order_failed=db_integration.notify_order_failed
        ),
        is_active=True
    )

@router.put("/", response_model=DiscordIntegrationResponse)
async def update_discord_integration(
    integration: DiscordIntegrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update Discord integration settings."""
    logger.info(f"UPDATE DISCORD INTEGRATION ROUTE CALLED by user {current_user.email}")
    logger.debug(f"Update details: {integration}")
    
    # Update integration
    db_integration = await DiscordService.update_integration(db, integration, current_user)
    
    # Convert to response model
    return DiscordIntegrationResponse(
        id=db_integration.id,
        user_id=db_integration.user_id,
        webhook=WebhookConfig(
            url=db_integration.webhook_url,
            username=db_integration.webhook_username,
            avatar_url=db_integration.webhook_avatar_url
        ),
        notifications=NotificationConfig(
            order_created=db_integration.notify_order_created,
            order_updated=db_integration.notify_order_updated,
            order_completed=db_integration.notify_order_completed,
            order_failed=db_integration.notify_order_failed
        ),
        is_active=True
    )

@router.delete("/")
async def delete_discord_integration(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete Discord integration."""
    logger.info(f"DELETE DISCORD INTEGRATION ROUTE CALLED by user {current_user.email}")
    success = await DiscordService.delete_integration(db, current_user)
    if success:
        return {"message": "Discord integration deleted successfully"}
    raise HTTPException(status_code=404, detail="Discord integration not found")
