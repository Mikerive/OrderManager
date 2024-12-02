from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from core.orders.models import Order as BaseOrder, OrderCreate, OrderUpdate
from core.orders.service import OrderService as BaseOrderService
from core.user.models import User
from .models import ManagedOrder, ManagedOrderDB, OrderStatus, OrderPriority
from core.exceptions import OrderNotFoundError, UnauthorizedError
from fastapi import HTTPException

class OrderService:
    """Service for managing orders with extended functionality."""

    @staticmethod
    async def create_order(db: Session, user_id: int, order_data: dict) -> ManagedOrder:
        """Create a new managed order."""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError()

        # Create managed order
        managed_order = ManagedOrderDB(
            owner_id=user.id,
            title=order_data["title"],
            description=order_data.get("description"),
            status=order_data.get("status", "pending"),
            priority=order_data.get("priority", OrderPriority.MEDIUM),
            tags=",".join(order_data.get("tags", [])),
            estimated_hours=order_data.get("estimated_hours"),
            notes=order_data.get("notes"),
            dependencies=order_data.get("dependencies", [])
        )

        # Add to database
        db.add(managed_order)
        db.commit()
        db.refresh(managed_order)

        # Convert to Pydantic model and return
        return ManagedOrder.model_validate(managed_order)

    @staticmethod
    async def get_order(db: Session, order_id: int, user_id: int) -> ManagedOrder:
        """Get a specific order."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError()

        # Get managed order
        managed_order = db.query(ManagedOrderDB).filter(
            ManagedOrderDB.id == order_id,
            ManagedOrderDB.owner_id == user_id
        ).first()

        if not managed_order:
            raise OrderNotFoundError(order_id=order_id)

        # Convert to Pydantic model and return
        return ManagedOrder.model_validate(managed_order)

    @staticmethod
    async def update_order(db: Session, order_id: int, user_id: int, update_data: dict) -> ManagedOrder:
        """Update an existing order."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError()

        # Get managed order
        managed_order = db.query(ManagedOrderDB).filter(
            ManagedOrderDB.id == order_id,
            ManagedOrderDB.owner_id == user_id
        ).first()

        if not managed_order:
            raise OrderNotFoundError(order_id=order_id)

        # Update fields
        for key, value in update_data.items():
            if value is not None:
                if key == "tags" and isinstance(value, list):
                    value = ",".join(value)
                setattr(managed_order, key, value)

        # Update in database
        db.add(managed_order)
        db.commit()
        db.refresh(managed_order)

        # Convert to Pydantic model and return
        return ManagedOrder.model_validate(managed_order)

    @staticmethod
    async def delete_order(db: Session, order_id: int, user_id: int) -> None:
        """Delete an order."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError()

        # Get managed order
        managed_order = db.query(ManagedOrderDB).filter(
            ManagedOrderDB.id == order_id,
            ManagedOrderDB.owner_id == user_id
        ).first()

        if not managed_order:
            raise OrderNotFoundError(order_id=order_id)

        # Delete from database
        db.delete(managed_order)
        db.commit()

    @staticmethod
    async def list_user_orders(db: Session, user_id: int) -> List[ManagedOrder]:
        """List all orders for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError()

        # Get all managed orders for user
        managed_orders = db.query(ManagedOrderDB).filter(
            ManagedOrderDB.owner_id == user_id
        ).all()

        # Convert to Pydantic models and return
        return [ManagedOrder.model_validate(order) for order in managed_orders]

    @staticmethod
    async def get_orders(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[ManagedOrder]:
        """Get all orders for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError()

        # Get all managed orders for user
        managed_orders = db.query(ManagedOrderDB).filter(
            ManagedOrderDB.owner_id == user_id
        ).offset(skip).limit(limit).all()

        # Convert to Pydantic models and return
        return [ManagedOrder.model_validate(order) for order in managed_orders]

    @staticmethod
    async def update_order_status(db: Session, order_id: int, user_id: int, status: OrderStatus) -> ManagedOrder:
        """Update order status with appropriate timestamps."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError()

        # Get managed order
        managed_order = db.query(ManagedOrderDB).filter(
            ManagedOrderDB.id == order_id,
            ManagedOrderDB.owner_id == user_id
        ).first()

        if not managed_order:
            raise OrderNotFoundError(order_id=order_id)

        old_status = managed_order.status
        managed_order.status = status

        # Update timestamps based on status changes
        if status == OrderStatus.IN_PROGRESS and old_status != OrderStatus.IN_PROGRESS:
            managed_order.started_at = datetime.utcnow()
        elif status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.FAILED]:
            managed_order.completed_at = datetime.utcnow()

        # Update in database
        db.add(managed_order)
        db.commit()
        db.refresh(managed_order)

        # Convert to Pydantic model and return
        return ManagedOrder.model_validate(managed_order)

    @staticmethod
    async def search_orders(
        db: Session,
        user_id: Optional[int] = None,
        status: Optional[OrderStatus] = None,
        priority: Optional[OrderPriority] = None,
        tags: Optional[List[str]] = None,
        search_term: Optional[str] = None
    ) -> List[ManagedOrder]:
        """Search orders with various filters."""
        query = db.query(ManagedOrderDB)

        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UnauthorizedError()
            query = query.filter(ManagedOrderDB.owner_id == user_id)
        if status:
            query = query.filter(ManagedOrderDB.status == status)
        if priority:
            query = query.filter(ManagedOrderDB.priority == priority)
        if tags:
            # Search for orders that have any of the specified tags
            tag_filters = []
            for tag in tags:
                tag_filters.append(ManagedOrderDB.tags.like(f"%{tag}%"))
            query = query.filter(or_(*tag_filters))
        if search_term:
            # Search in title and description
            search_filter = or_(
                ManagedOrderDB.title.ilike(f"%{search_term}%"),
                ManagedOrderDB.description.ilike(f"%{search_term}%")
            )
            query = query.filter(search_filter)

        # Get all managed orders
        managed_orders = query.all()

        # Convert to Pydantic models and return
        return [ManagedOrder.model_validate(order) for order in managed_orders]

    @staticmethod
    async def get_order_statistics(db: Session, user_id: Optional[int] = None) -> dict:
        """Get statistics about orders."""
        query = db.query(ManagedOrderDB)
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UnauthorizedError()
            query = query.filter(ManagedOrderDB.owner_id == user_id)

        total_orders = query.count()
        status_counts = {
            status.value: query.filter(ManagedOrderDB.status == status).count()
            for status in OrderStatus
        }
        priority_counts = {
            priority.value: query.filter(ManagedOrderDB.priority == priority).count()
            for priority in OrderPriority
        }

        # Calculate completion rate
        completed = status_counts[OrderStatus.COMPLETED.value]
        completion_rate = (completed / total_orders * 100) if total_orders > 0 else 0

        return {
            "total_orders": total_orders,
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "completion_rate": completion_rate
        }
