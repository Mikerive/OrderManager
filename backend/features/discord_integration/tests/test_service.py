import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.orm import Session
from fastapi import HTTPException

from core.models import User, DiscordIntegration
from core.testing import test_db, test_user
from ..service import DiscordService
from ..models import (
    DiscordIntegrationCreate,
    DiscordIntegrationUpdate,
    WebhookConfig,
    NotificationConfig
)

@pytest.mark.asyncio
async def test_create_integration(test_db: Session, test_user: User):
    """Test Discord integration creation."""
    integration_data = DiscordIntegrationCreate(
        webhook=WebhookConfig(
            url="https://discord.com/api/webhooks/test",
            username="Test Bot",
            avatar_url="https://example.com/avatar.png"
        ),
        notifications=NotificationConfig(
            order_created=True,
            order_updated=True,
            order_completed=True,
            order_failed=True
        )
    )

    with patch('features.discord_integration.service.DiscordService._verify_webhook', new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = True
        try:
            integration = await DiscordService.create_integration(
                test_db,
                integration_data,
                test_user
            )
            assert integration.webhook_username == "Test Bot"
            assert integration.notify_order_created is True
            assert integration.user_id == test_user.id
        except Exception as e:
            assert False, f"An error occurred: {e}"

@pytest.mark.asyncio
async def test_get_integration(test_db: Session, test_user: User):
    """Test getting Discord integration."""
    integration = DiscordIntegration(
        user_id=test_user.id,
        webhook_url="https://discord.com/api/webhooks/test",
        webhook_username="Test Bot"
    )
    test_db.add(integration)
    test_db.commit()

    try:
        result = await DiscordService.get_integration(test_db, test_user)
        assert result.webhook_username == "Test Bot"
        assert result.user_id == test_user.id
    except Exception as e:
        assert False, f"An error occurred: {e}"

@pytest.mark.asyncio
async def test_update_integration(test_db: Session, test_user: User):
    """Test updating Discord integration."""
    integration = DiscordIntegration(
        user_id=test_user.id,
        webhook_url="https://discord.com/api/webhooks/test",
        webhook_username="Original Bot",
        notify_order_completed=True
    )
    test_db.add(integration)
    test_db.commit()

    update_data = DiscordIntegrationUpdate(
        webhook=WebhookConfig(
            url="https://discord.com/api/webhooks/test2",
            username="Updated Bot"
        ),
        notifications=NotificationConfig(
            order_completed=False
        )
    )

    with patch('features.discord_integration.service.DiscordService._verify_webhook', new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = True
        try:
            updated = await DiscordService.update_integration(
                test_db,
                update_data,
                test_user
            )
            assert updated.webhook_username == "Updated Bot"
            assert updated.notify_order_completed is False
        except Exception as e:
            assert False, f"An error occurred: {e}"

@pytest.mark.asyncio
async def test_delete_integration(test_db: Session, test_user: User):
    """Test deleting Discord integration."""
    integration = DiscordIntegration(
        user_id=test_user.id,
        webhook_url="https://discord.com/api/webhooks/test",
        webhook_username="Test Bot"
    )
    test_db.add(integration)
    test_db.commit()

    try:
        success = await DiscordService.delete_integration(test_db, test_user)
        assert success is True
    except Exception as e:
        assert False, f"An error occurred: {e}"

    # Verify integration was deleted
    result = test_db.query(DiscordIntegration).filter(
        DiscordIntegration.user_id == test_user.id
    ).first()
    assert result is None

@pytest.mark.asyncio
async def test_send_notification():
    """Test sending Discord notification."""
    webhook_url = "https://discord.com/api/webhooks/test"
    content = "Test notification"
    username = "Test Bot"
    avatar_url = "https://example.com/avatar.png"

    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        # Test successful notification
        mock_post.return_value.status_code = 204
        try:
            success = await DiscordService.send_notification(
                webhook_url=webhook_url,
                content=content,
                username=username,
                avatar_url=avatar_url
            )
            assert success is True
            mock_post.assert_called_once()
        except Exception as e:
            assert False, f"An error occurred: {e}"
        
        # Test failed notification
        mock_post.reset_mock()
        mock_post.return_value.status_code = 404
        try:
            success = await DiscordService.send_notification(
                webhook_url=webhook_url,
                content=content
            )
            assert success is False
            mock_post.assert_called_once()
        except Exception as e:
            assert False, f"An error occurred: {e}"
        
        # Test network error
        mock_post.reset_mock()
        mock_post.side_effect = Exception("Network error")
        try:
            success = await DiscordService.send_notification(
                webhook_url=webhook_url,
                content=content
            )
            assert success is False
            mock_post.assert_called_once()
        except Exception as e:
            assert False, f"An error occurred: {e}"

@pytest.mark.asyncio
async def test_verify_webhook():
    """Test webhook URL verification."""
    webhook_url = "https://discord.com/api/webhooks/test"

    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        # Test valid webhook
        mock_get.return_value.status_code = 200
        try:
            is_valid = await DiscordService._verify_webhook(webhook_url)
            assert is_valid is True
            mock_get.assert_called_once()
        except Exception as e:
            assert False, f"An error occurred: {e} # Fixed syntax error here"
        
        # Test invalid webhook
        mock_get.reset_mock()
        mock_get.return_value.status_code = 404
        try:
            is_valid = await DiscordService._verify_webhook(webhook_url)
            assert is_valid is False
            mock_get.assert_called_once()
        except Exception as e:
            assert False, f"An error occurred: {e}"
        
        # Test network error
        mock_get.reset_mock()
        mock_get.side_effect = Exception("Network error")
        try:
            is_valid = await DiscordService._verify_webhook(webhook_url)
            assert is_valid is False
            mock_get.assert_called_once()
        except Exception as e:
            assert False, f"An error occurred: {e}"
