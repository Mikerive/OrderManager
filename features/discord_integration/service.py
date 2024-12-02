from typing import Optional
import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.models import User, DiscordIntegration
from .models import DiscordIntegrationCreate, DiscordIntegrationUpdate

class DiscordService:
    """Service for handling Discord integration operations."""
    
    @staticmethod
    async def create_integration(
        db: Session,
        integration: DiscordIntegrationCreate,
        current_user: User
    ) -> DiscordIntegration:
        """Create a new Discord integration."""
        # Verify webhook URL
        if not await DiscordService._verify_webhook(integration.webhook.url):
            raise HTTPException(
                status_code=400,
                detail="Invalid Discord webhook URL"
            )
        
        db_integration = DiscordIntegration(
            user_id=current_user.id,
            webhook_url=str(integration.webhook.url),
            webhook_username=integration.webhook.username,
            webhook_avatar_url=str(integration.webhook.avatar_url) if integration.webhook.avatar_url else None,
            notify_order_created=integration.notifications.order_created,
            notify_order_updated=integration.notifications.order_updated,
            notify_order_completed=integration.notifications.order_completed,
            notify_order_failed=integration.notifications.order_failed
        )
        
        try:
            db.add(db_integration)
            db.commit()
            db.refresh(db_integration)
            return db_integration
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Discord integration already exists for this user"
            )
    
    @staticmethod
    async def get_integration(
        db: Session,
        current_user: User
    ) -> Optional[DiscordIntegration]:
        """Get Discord integration for the current user."""
        return db.query(DiscordIntegration).filter(
            DiscordIntegration.user_id == current_user.id
        ).first()
    
    @staticmethod
    async def update_integration(
        db: Session,
        integration_update: DiscordIntegrationUpdate,
        current_user: User
    ) -> DiscordIntegration:
        """Update Discord integration settings."""
        db_integration = await DiscordService.get_integration(db, current_user)
        if not db_integration:
            raise HTTPException(
                status_code=404,
                detail="Discord integration not found"
            )
        
        if integration_update.webhook:
            # Verify new webhook URL if provided
            if not await DiscordService._verify_webhook(integration_update.webhook.url):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid Discord webhook URL"
                )
            db_integration.webhook_url = str(integration_update.webhook.url)
            db_integration.webhook_username = integration_update.webhook.username
            db_integration.webhook_avatar_url = str(integration_update.webhook.avatar_url) if integration_update.webhook.avatar_url else None
        
        if integration_update.notifications:
            db_integration.notify_order_created = integration_update.notifications.order_created
            db_integration.notify_order_updated = integration_update.notifications.order_updated
            db_integration.notify_order_completed = integration_update.notifications.order_completed
            db_integration.notify_order_failed = integration_update.notifications.order_failed
        
        try:
            db.commit()
            db.refresh(db_integration)
            return db_integration
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Invalid integration data"
            )
    
    @staticmethod
    async def delete_integration(db: Session, current_user: User) -> bool:
        """Delete Discord integration."""
        db_integration = await DiscordService.get_integration(db, current_user)
        if not db_integration:
            raise HTTPException(
                status_code=404,
                detail="Discord integration not found"
            )
        
        try:
            db.delete(db_integration)
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Could not delete Discord integration"
            )
    
    @staticmethod
    async def send_notification(
        webhook_url: str,
        content: str,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> bool:
        """Send a notification to Discord webhook."""
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "content": content,
                    "username": username,
                    "avatar_url": avatar_url
                }
                response = await client.post(webhook_url, json=payload)
                return response.status_code == 204
            except Exception:
                return False
    
    @staticmethod
    async def _verify_webhook(webhook_url: str) -> bool:
        """Verify that a Discord webhook URL is valid."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(webhook_url)
                return response.status_code == 200
            except Exception:
                return False
