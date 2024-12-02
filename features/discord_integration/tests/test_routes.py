import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import AsyncMock, patch

from core.models import DiscordIntegration

@pytest.mark.asyncio
async def test_create_discord_integration(client: TestClient, auth_headers: dict):
    """Test creating Discord integration."""
    with patch('features.discord_integration.service.DiscordService._verify_webhook', new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = True
        response = client.post(
            "/api/discord",
            headers=auth_headers,
            json={
                "webhook": {
                    "url": "https://discord.com/api/webhooks/test",
                    "username": "Test Bot",
                    "avatar_url": "https://example.com/avatar.png"
                },
                "notifications": {
                    "order_created": True,
                    "order_updated": True,
                    "order_completed": True,
                    "order_failed": True
                }
            }
        )
        assert response.status_code == 200
        
        # Check response structure
        response_json = response.json()
        assert "id" in response_json
        assert "user_id" in response_json
        assert "is_active" in response_json
        
        # Check webhook details
        assert response_json["webhook"]["url"] == "https://discord.com/api/webhooks/test"
        assert response_json["webhook"]["username"] == "Test Bot"
        assert response_json["webhook"]["avatar_url"] == "https://example.com/avatar.png"
        
        # Check notifications
        assert response_json["notifications"]["order_created"] == True
        assert response_json["notifications"]["order_updated"] == True
        assert response_json["notifications"]["order_completed"] == True
        assert response_json["notifications"]["order_failed"] == True

@pytest.mark.asyncio
async def test_get_discord_integration(
    client: TestClient,
    test_db: Session,
    auth_headers: dict
):
    """Test getting Discord integration."""
    # Delete any existing integrations for the user first
    existing_integration = test_db.query(DiscordIntegration).filter_by(user_id=1).first()
    if existing_integration:
        test_db.delete(existing_integration)
        test_db.commit()

    integration = DiscordIntegration(
        user_id=1,
        webhook_url="https://discord.com/api/webhooks/test",
        webhook_username="Test Bot",
        webhook_avatar_url="https://example.com/avatar.png",
        notify_order_created=True,
        notify_order_updated=True,
        notify_order_completed=True,
        notify_order_failed=True
    )
    test_db.add(integration)
    test_db.commit()

    response = client.get("/api/discord", headers=auth_headers)
    assert response.status_code == 200
    
    # Check response structure
    response_json = response.json()
    assert "id" in response_json
    assert "user_id" in response_json
    assert "is_active" in response_json
    
    # Check webhook details
    assert response_json["webhook"]["url"] == "https://discord.com/api/webhooks/test"
    assert response_json["webhook"]["username"] == "Test Bot"
    assert response_json["webhook"]["avatar_url"] == "https://example.com/avatar.png"
    
    # Check notifications
    assert response_json["notifications"]["order_created"] == True
    assert response_json["notifications"]["order_updated"] == True
    assert response_json["notifications"]["order_completed"] == True
    assert response_json["notifications"]["order_failed"] == True

@pytest.mark.asyncio
async def test_update_discord_integration(
    client: TestClient,
    test_db: Session,
    auth_headers: dict
):
    """Test updating Discord integration."""
    # Delete any existing integrations for the user first
    existing_integration = test_db.query(DiscordIntegration).filter_by(user_id=1).first()
    if existing_integration:
        test_db.delete(existing_integration)
        test_db.commit()

    integration = DiscordIntegration(
        user_id=1,
        webhook_url="https://discord.com/api/webhooks/test",
        webhook_username="Original Bot",
        webhook_avatar_url="https://example.com/avatar.png",
        notify_order_created=True,
        notify_order_updated=True,
        notify_order_completed=True,
        notify_order_failed=True
    )
    test_db.add(integration)
    test_db.commit()

    with patch('features.discord_integration.service.DiscordService._verify_webhook', new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = True
        response = client.put(
            "/api/discord",
            headers=auth_headers,
            json={
                "webhook": {
                    "url": "https://discord.com/api/webhooks/test2",
                    "username": "Updated Bot"
                },
                "notifications": {
                    "order_completed": False
                }
            }
        )

        assert response.status_code == 200
        
        # Check response structure
        response_json = response.json()
        assert "id" in response_json
        assert "user_id" in response_json
        assert "is_active" in response_json
        
        # Check webhook details
        assert response_json["webhook"]["url"] == "https://discord.com/api/webhooks/test2"
        assert response_json["webhook"]["username"] == "Updated Bot"
        assert response_json["webhook"]["avatar_url"] is None
        
        # Check notifications
        assert response_json["notifications"]["order_created"] == True
        assert response_json["notifications"]["order_updated"] == True
        assert response_json["notifications"]["order_completed"] == False
        assert response_json["notifications"]["order_failed"] == True

@pytest.mark.asyncio
async def test_delete_discord_integration(
    client: TestClient,
    test_db: Session,
    auth_headers: dict
):
    """Test deleting Discord integration."""
    # Delete any existing integrations for the user first
    existing_integration = test_db.query(DiscordIntegration).filter_by(user_id=1).first()
    if existing_integration:
        test_db.delete(existing_integration)
        test_db.commit()

    integration = DiscordIntegration(
        user_id=1,
        webhook_url="https://discord.com/api/webhooks/test",
        webhook_username="Test Bot"
    )
    test_db.add(integration)
    test_db.commit()

    response = client.delete("/api/discord", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Discord integration deleted successfully"}
