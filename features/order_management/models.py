from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, validator
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Table, Enum as SQLAlchemyEnum, JSON
from sqlalchemy.orm import relationship, declarative_base
import enum

from core.orders.models import Order as BaseOrder, OrderNode
from core.database.database import Base

class OrderPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"

class OrderChainType(str, enum.Enum):
    LINEAR = "linear"
    BRANCHING = "branching"

class ExchangeType(str, enum.Enum):
    ALPACA = "alpaca"
    PAPER = "paper"  # Paper trading simulation
    # Add more exchanges as needed
    # BINANCE = "binance"
    # COINBASE = "coinbase"

class ExchangeConfig(BaseModel):
    """Configuration for an exchange."""
    exchange_type: ExchangeType
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    paper_trading: bool = False
    additional_settings: Dict[str, Any] = Field(default_factory=dict)

class ManagedOrderDB(BaseOrder):
    """SQLAlchemy model for managed orders."""
    __tablename__ = "managed_orders"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, ForeignKey("orders.id"), primary_key=True)
    priority = Column(SQLAlchemyEnum(OrderPriority), default=OrderPriority.MEDIUM)
    tags = Column(String, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    exchange_type = Column(String, nullable=False, default=ExchangeType.PAPER)
    exchange_config = Column(JSON, nullable=True)
    
    # Chain management fields
    chain_status = Column(String, nullable=True)  # Status of the entire chain
    chain_error = Column(String, nullable=True)  # Error message if chain fails
    chain_metadata = Column(JSON, nullable=True)  # Additional chain-specific data

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
    exchange_type: ExchangeType = ExchangeType.PAPER
    exchange_config: Optional[ExchangeConfig] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[int] = Field(default_factory=list)

    # Chain-related fields
    chain_id: Optional[str] = Field(None, description="ID of the order chain this order belongs to")
    chain_type: Optional[str] = Field(None, description="Type of the order chain")
    chain_sequence: Optional[int] = Field(None, description="Order sequence in the chain")
    parent_order_id: Optional[int] = Field(None, description="ID of the parent order in the chain")
    chain_status: Optional[str] = Field(None, description="Status of the entire chain")
    chain_error: Optional[str] = Field(None, description="Error message if chain fails")
    chain_metadata: Optional[dict] = Field(None, description="Additional chain-specific data")

    @validator("chain_type")
    def validate_chain_type(cls, v):
        if v and v not in OrderChainType.__members__:
            raise ValueError(f"Invalid chain type. Must be one of: {list(OrderChainType.__members__.keys())}")
        return v

    @field_validator("tags", mode="before")
    def split_tags(cls, v):
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(",") if tag.strip()]
        return v

    @field_validator("dependencies", mode="before")
    def split_dependencies(cls, v):
        if isinstance(v, str):
            return [int(x) for x in v.split(",")] if v else []
        return v

class ManagedOrderBase(OrderNode):
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

    title: str
    description: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    priority: OrderPriority = OrderPriority.MEDIUM
    tags: List[str] = Field(default_factory=list)
    estimated_hours: Optional[float] = None
    notes: Optional[str] = None
    exchange_type: ExchangeType = ExchangeType.PAPER
    exchange_config: Optional[ExchangeConfig] = None
    dependencies: Optional[List[int]] = Field(default=[], description="List of order IDs that this order depends on")
    symbol: str
    quantity: float
    order_type: str
    side: str
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: Optional[str] = "day"
    extended_hours: Optional[bool] = False

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
    provider_order_id: Optional[str] = None

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
