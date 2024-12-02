from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Table, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, declarative_base
import enum

from core.orders.models import Order as BaseOrder, OrderBase
from core.database.database import Base

class OrderPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class OrderStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class ManagedOrderDB(BaseOrder):
    """SQLAlchemy model for managed orders."""
    __tablename__ = "managed_orders"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, ForeignKey("orders.id"), primary_key=True)
    priority = Column(SQLAlchemyEnum(OrderPriority), default=OrderPriority.MEDIUM)
    tags = Column(String, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    notes = Column(String, nullable=True)

class ManagedOrder(BaseModel):
    """Pydantic model for managed orders."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    owner_id: int
    title: str
    description: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    priority: OrderPriority = OrderPriority.MEDIUM
    tags: List[str] = Field(default_factory=list)
    estimated_hours: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[int] = Field(default_factory=list)

    @field_validator("tags", mode="before")
    def split_tags(cls, v):
        if isinstance(v, str):
            return v.split(",") if v else []
        return v

    @field_validator("dependencies", mode="before")
    def split_dependencies(cls, v):
        if isinstance(v, str):
            return [int(x) for x in v.split(",")] if v else []
        return v

class ManagedOrderBase(OrderBase):
    """Extended base model for managed orders."""
    model_config = ConfigDict(from_attributes=True)

    priority: Optional[OrderPriority] = Field(OrderPriority.MEDIUM, description="Order priority level")
    tags: Optional[List[str]] = Field(default=[], description="List of tags for categorization")
    estimated_hours: Optional[str] = Field(None, description="Estimated hours to complete")
    actual_hours: Optional[str] = Field(None, description="Actual hours spent")
    notes: Optional[str] = Field(None, description="Additional notes about the order")

class ManagedOrderCreate(ManagedOrderBase):
    """Model for creating a managed order."""
    model_config = ConfigDict(from_attributes=True)

    status: OrderStatus = Field(OrderStatus.DRAFT, description="Initial order status")
    dependencies: Optional[List[int]] = Field(default=[], description="List of order IDs that this order depends on")

class ManagedOrderUpdate(ManagedOrderBase):
    """Model for updating a managed order."""
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[OrderStatus] = None
    priority: Optional[OrderPriority] = None
    dependencies: Optional[List[int]] = None

class ManagedOrderResponse(ManagedOrderBase):
    """Model for managed order responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    owner_id: int
    dependencies: List[int] = []

class OrderCreate(BaseModel):
    """Model for creating a new order."""
    model_config = ConfigDict(from_attributes=True)

    title: str
    description: Optional[str] = None
    status: str = "pending"
    dependencies: List[int] = []

class OrderUpdate(BaseModel):
    """Model for updating an existing order."""
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    estimated_hours: Optional[float] = None
    notes: Optional[str] = None
    dependencies: Optional[List[int]] = None
