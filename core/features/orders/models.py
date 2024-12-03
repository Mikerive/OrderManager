from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Table, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from core.database.database import Base
from enum import Enum

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    """Status of an order."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    FILLED = "filled"
    COMPLETED = "completed"
    EXPIRED = "expired"
    REPLACED = "replaced"

class OrderConditionType(str, Enum):
    """Types of conditions that can exist between orders."""
    FILL = "fill"  # Execute when the parent order is filled
    CANCEL = "cancel"  # Cancel when the parent order is filled
    PRICE_TARGET = "price_target"  # Execute when price target is hit
    BRACKET_TAKE_PROFIT = "bracket_take_profit"  # Take profit order in a bracket
    BRACKET_STOP_LOSS = "bracket_stop_loss"  # Stop loss order in a bracket
    OCO_PAIR = "oco_pair"  # Part of an OCO (One-Cancels-Other) pair
    CHAIN_NEXT = "chain_next"  # Next order in a chain sequence
    TECHNICAL_INDICATOR = "technical_indicator"  # Execute based on technical indicator

class OrderChainType(str, Enum):
    """Types of order chains."""
    BRACKET = "bracket"  # Bracket order (entry + take profit + stop loss)
    OCO = "oco"  # One-Cancels-Other order pair
    SEQUENTIAL = "sequential"  # Sequential chain of orders
    CONDITIONAL = "conditional"  # Orders with custom conditions

# Association table for order dependencies (edges in the graph)
order_dependencies = Table(
    "order_dependencies",
    Base.metadata,
    Column("dependent_order_id", Integer, ForeignKey("orders.id"), primary_key=True),
    Column("dependency_order_id", Integer, ForeignKey("orders.id"), primary_key=True),
    Column("condition_type", String),  # e.g., "fill", "cancel", "price_target"
    Column("condition_data", JSON),  # Store condition-specific data
)

class Order(Base):
    """
    Order model representing orders in the system. Acts as a node in the order graph.
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(String, default=OrderStatus.PENDING)
    order_type = Column(String)
    side = Column(String)
    symbol = Column(String)
    quantity = Column(Float)
    filled_quantity = Column(Float, default=0)
    price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    limit_price = Column(Float, nullable=True)
    trail_percent = Column(Float, nullable=True)
    trail_price = Column(Float, nullable=True)
    additional_data = Column(JSON, nullable=True)  # Store provider-specific data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    provider = Column(String)  # e.g., "alpaca", "binance", etc.
    provider_order_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # Chain-related fields
    chain_id = Column(String, nullable=True, index=True)  # Unique ID for the order chain
    chain_type = Column(String, nullable=True)  # Type of chain this order belongs to
    chain_sequence = Column(Integer, nullable=True)  # Order sequence in the chain
    parent_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)  # Direct parent in the chain

    # Relationships
    owner = relationship("User", backref="orders")
    dependencies = relationship(
        "Order",
        secondary=order_dependencies,
        primaryjoin=id == order_dependencies.c.dependent_order_id,
        secondaryjoin=id == order_dependencies.c.dependency_order_id,
        backref="dependent_orders",
    )

class OrderEdge(BaseModel):
    """Represents an edge between two orders in the order graph."""
    from_order_id: int
    to_order_id: int
    condition_type: str
    condition_data: Dict[str, Any] = {}

class OrderNode(BaseModel):
    """Base model for Order data."""
    title: str = Field(..., description="Title of the order")
    description: Optional[str] = Field(None, description="Detailed description of the order")
    status: OrderStatus = Field(OrderStatus.PENDING, description="Current status of the order")
    order_type: OrderType
    side: OrderSide
    symbol: str
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    limit_price: Optional[float] = None
    trail_percent: Optional[float] = None
    trail_price: Optional[float] = None
    provider: str
    additional_data: Optional[Dict[str, Any]] = None

class OrderCreate(OrderNode):
    """Model for creating a new order."""
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    order_type: OrderType
    side: OrderSide
    symbol: str
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    limit_price: Optional[float] = None
    trail_percent: Optional[float] = None
    trail_price: Optional[float] = None
    provider: str
    additional_data: Optional[Dict[str, Any]] = None
    dependencies: List[OrderEdge] = []
    provider_order_id: Optional[str] = None

    model_config = {"extra": "allow"}

class OrderUpdate(BaseModel):
    """Model for updating an existing order."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[OrderStatus] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    stop_price: Optional[float] = None
    limit_price: Optional[float] = None
    trail_percent: Optional[float] = None
    trail_price: Optional[float] = None
    additional_data: Optional[Dict[str, Any]] = None
    dependencies: Optional[List[OrderEdge]] = None

class OrderResponse(OrderNode):
    """Model for order responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int
    provider_order_id: Optional[str] = None
    filled_quantity: float = 0
    is_active: bool = True
    dependencies: List[OrderEdge] = Field(default_factory=list)
    dependent_orders: List[OrderEdge] = Field(default_factory=list)

    class Config:
        orm_mode = True
