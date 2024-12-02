from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from core.database.database import Base

# Association table for order dependencies
order_dependencies = Table(
    "order_dependencies",
    Base.metadata,
    Column("dependent_order_id", Integer, ForeignKey("orders.id"), primary_key=True),
    Column("dependency_order_id", Integer, ForeignKey("orders.id"), primary_key=True),
)


class Order(Base):
    """
    Order model representing orders in the system.

    Attributes:
        id (int): Unique identifier for the order
        title (str): Title of the order
        description (str): Detailed description of the order
        status (str): Current status of the order
        created_at (DateTime): Timestamp of order creation
        updated_at (DateTime): Timestamp of last order update
        owner_id (int): ID of the user who created the order

        Relationships:
        - owner: User who created the order
        - dependencies: Other orders this order depends on
        - dependent_orders: Orders that depend on this order
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    owner = relationship("User", backref="orders")
    dependencies = relationship(
        "Order",
        secondary=order_dependencies,
        primaryjoin=id == order_dependencies.c.dependent_order_id,
        secondaryjoin=id == order_dependencies.c.dependency_order_id,
        backref="dependent_orders",
    )


# Pydantic Models
class OrderBase(BaseModel):
    """Base model for Order data."""

    title: str = Field(..., description="Title of the order")
    description: Optional[str] = Field(
        None, description="Detailed description of the order"
    )
    status: str = Field("pending", description="Current status of the order")


class OrderCreate(OrderBase):
    """Model for creating a new order."""

    dependencies: Optional[List[int]] = Field(
        default=[], description="List of order IDs that this order depends on"
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
        orm_mode = True
