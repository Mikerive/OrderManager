from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base

# Association table for order dependencies
order_dependencies = Table(
    'order_dependencies',
    Base.metadata,
    Column('dependent_order_id', Integer, ForeignKey('orders.id'), primary_key=True),
    Column('dependency_order_id', Integer, ForeignKey('orders.id'), primary_key=True)
)

class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    orders = relationship("Order", back_populates="owner")
    discord_integration = relationship("DiscordIntegration", back_populates="user", uselist=False)
    log_entries = relationship("LogEntry", back_populates="user")

class Order(Base):
    """Order model."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(String)  # pending, active, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", back_populates="orders")
    dependencies = relationship(
        "Order",
        secondary=order_dependencies,
        primaryjoin=id==order_dependencies.c.dependent_order_id,
        secondaryjoin=id==order_dependencies.c.dependency_order_id,
        backref="dependent_orders"
    )

class DiscordIntegration(Base):
    """Discord integration model."""
    __tablename__ = "discord_integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    webhook_url = Column(String)
    webhook_username = Column(String, nullable=True)
    webhook_avatar_url = Column(String, nullable=True)
    
    # Notification preferences
    notify_order_created = Column(Boolean, default=True)
    notify_order_updated = Column(Boolean, default=True)
    notify_order_completed = Column(Boolean, default=True)
    notify_order_failed = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="discord_integration")

class LogEntry(Base):
    """Log entry model."""
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String)  # INFO, WARNING, ERROR, etc.
    message = Column(String)
    source = Column(String)  # The source of the log (e.g., service name, function)
    log_metadata = Column(String, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="log_entries")
