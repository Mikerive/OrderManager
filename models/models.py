from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Association table for order dependencies
order_dependencies = Table(
    'order_dependencies',
    Base.metadata,
    Column('dependent_order_id', Integer, ForeignKey('orders.id'), primary_key=True),
    Column('dependency_order_id', Integer, ForeignKey('orders.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    orders = relationship("Order", back_populates="owner")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    status = Column(String)  # pending, active, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="orders")
    dependencies = relationship(
        "Order",
        secondary=order_dependencies,
        primaryjoin=id==order_dependencies.c.dependent_order_id,
        secondaryjoin=id==order_dependencies.c.dependency_order_id,
        backref="dependent_orders"
    )
