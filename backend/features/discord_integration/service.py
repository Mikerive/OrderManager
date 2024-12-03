import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import DiscordIntegration
from .schemas import (
    DiscordIntegrationCreate, 
    DiscordIntegrationResponse, 
    DiscordIntegrationUpdate,
    WebhookConfig,
    NotificationConfig
)

class DiscordService:
    """Service for managing Discord integrations."""

    def __init__(self, db: Session):
        """
        Initialize the Discord service.
        
        Args:
            db (Session): Database session
        """
        self.db = db

    async def _verify_webhook(self, webhook_url: str) -> bool:
        """
        Verify the Discord webhook URL.
        
        Args:
            webhook_url (str): Webhook URL to verify
        
        Returns:
            bool: True if webhook is valid, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(webhook_url)
                return response.status_code == 200
        except Exception:
            return False

    async def create_integration(
        self, 
        user_id: int, 
        integration: DiscordIntegrationCreate
    ) -> DiscordIntegrationResponse:
        """
        Create a Discord integration for a user.
        
        Args:
            user_id (int): ID of the user creating the integration
            integration (DiscordIntegrationCreate): Integration details
        
        Returns:
            DiscordIntegrationResponse: Created integration details
        """
        # Verify webhook
        if not await self._verify_webhook(integration.webhook.url):
            raise HTTPException(status_code=400, detail="Invalid Discord webhook URL")

        # Check if integration already exists
        existing = self.db.query(DiscordIntegration).filter_by(user_id=user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Discord integration already exists")

        # Create new integration
        db_integration = DiscordIntegration(
            user_id=user_id,
            webhook_url=integration.webhook.url,
            webhook_username=integration.webhook.username,
            webhook_avatar_url=integration.webhook.avatar_url,
            notify_order_created=integration.notifications.order_created,
            notify_order_updated=integration.notifications.order_updated,
            notify_order_completed=integration.notifications.order_completed,
            notify_order_failed=integration.notifications.order_failed
        )
        
        self.db.add(db_integration)
        self.db.commit()
        self.db.refresh(db_integration)

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

    async def get_integration(self, user_id: int) -> DiscordIntegrationResponse:
        """
        Get Discord integration for a user.
        
        Args:
            user_id (int): ID of the user
        
        Returns:
            DiscordIntegrationResponse: User's integration details
        """
        db_integration = self.db.query(DiscordIntegration).filter_by(user_id=user_id).first()
        
        if not db_integration:
            raise HTTPException(status_code=404, detail="Discord integration not found")

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

    async def update_integration(
        self, 
        user_id: int, 
        integration: DiscordIntegrationUpdate
    ) -> DiscordIntegrationResponse:
        """
        Update Discord integration for a user.
        
        Args:
            user_id (int): ID of the user
            integration (DiscordIntegrationUpdate): Updated integration details
        
        Returns:
            DiscordIntegrationResponse: Updated integration details
        """
        db_integration = self.db.query(DiscordIntegration).filter_by(user_id=user_id).first()
        
        if not db_integration:
            raise HTTPException(status_code=404, detail="Discord integration not found")

        # Verify webhook if URL is provided
        if integration.webhook and integration.webhook.url:
            if not await self._verify_webhook(integration.webhook.url):
                raise HTTPException(status_code=400, detail="Invalid Discord webhook URL")
            db_integration.webhook_url = integration.webhook.url

        # Update webhook details if provided
        if integration.webhook and integration.webhook.username:
            db_integration.webhook_username = integration.webhook.username
        if integration.webhook and integration.webhook.avatar_url:
            db_integration.webhook_avatar_url = integration.webhook.avatar_url

        # Update notification settings if provided
        if integration.notifications:
            if integration.notifications.order_created is not None:
                db_integration.notify_order_created = integration.notifications.order_created
            if integration.notifications.order_updated is not None:
                db_integration.notify_order_updated = integration.notifications.order_updated
            if integration.notifications.order_completed is not None:
                db_integration.notify_order_completed = integration.notifications.order_completed
            if integration.notifications.order_failed is not None:
                db_integration.notify_order_failed = integration.notifications.order_failed

        self.db.commit()
        self.db.refresh(db_integration)

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

    async def delete_integration(self, user_id: int) -> bool:
        """
        Delete Discord integration for a user.
        
        Args:
            user_id (int): ID of the user
        
        Returns:
            bool: True if integration was deleted, False otherwise
        """
        db_integration = self.db.query(DiscordIntegration).filter_by(user_id=user_id).first()
        
        if not db_integration:
            raise HTTPException(status_code=404, detail="Discord integration not found")

        self.db.delete(db_integration)
        self.db.commit()
        
        return True
