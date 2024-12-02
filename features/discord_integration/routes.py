from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.decorators import require_auth
from core.models import User

from .schemas import (
    DiscordIntegrationCreate, 
    DiscordIntegrationResponse, 
    DiscordIntegrationUpdate
)
from .service import DiscordService

router = APIRouter(prefix="/api/discord", tags=["discord"])

@router.post("", response_model=DiscordIntegrationResponse)
@require_auth
async def create_discord_integration(
    discord_integration: DiscordIntegrationCreate,
    db: Session = Depends(get_db),
    current_user: User = None
):
    """Create a Discord integration for the current user."""
    service = DiscordService(db)
    return await service.create_integration(current_user.id, discord_integration)

@router.get("", response_model=DiscordIntegrationResponse)
@require_auth
async def get_discord_integration(
    db: Session = Depends(get_db),
    current_user: User = None
):
    """Retrieve the Discord integration for the current user."""
    service = DiscordService(db)
    return await service.get_integration(current_user.id)

@router.put("", response_model=DiscordIntegrationResponse)
@require_auth
async def update_discord_integration(
    discord_integration: DiscordIntegrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = None
):
    """Update the Discord integration for the current user."""
    service = DiscordService(db)
    return await service.update_integration(current_user.id, discord_integration)

@router.delete("")
@require_auth
async def delete_discord_integration(
    db: Session = Depends(get_db),
    current_user: User = None
):
    """Delete the Discord integration for the current user."""
    service = DiscordService(db)
    await service.delete_integration(current_user.id)
    return {"message": "Discord integration deleted successfully"}
