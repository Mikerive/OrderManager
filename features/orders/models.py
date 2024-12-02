from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class OrderBase(BaseModel):
    """Base model for Order data."""
    title: str = Field(..., description="Title of the order")
    description: Optional[str] = Field(None, description="Detailed description of the order")
    status: str = Field("pending", description="Current status of the order")

class OrderCreate(OrderBase):
    """Model for creating a new order."""
    dependencies: Optional[List[int]] = Field(
        default=[],
        description="List of order IDs that this order depends on"
    )

class OrderUpdate(OrderBase):
    """Model for updating an existing order."""
    title: Optional[str] = None
    status: Optional[str] = None
    dependencies: Optional[List[int]] = None

class OrderResponse(OrderBase):
    """Model for order responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int
    dependencies: List[int] = []

    class Config:
        from_attributes = True
