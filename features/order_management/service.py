from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from core.orders.models import Order as BaseOrder, OrderCreate, OrderUpdate
from core.orders.service import OrderService as BaseOrderService
from core.user.models import User
from core.orders.events import OrderEventDispatcher, OrderEvent, OrderEventType
from .models import ManagedOrder, ManagedOrderDB, OrderStatus, OrderPriority, ExchangeType
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
            dependencies=order_data.get("dependencies", []),
            chain_id=order_data.get("chain_id"),
            chain_type=order_data.get("chain_type"),
            chain_sequence=order_data.get("chain_sequence"),
            parent_order_id=order_data.get("parent_order_id"),
            chain_status=order_data.get("chain_status"),
            chain_metadata=order_data.get("chain_metadata", {}),
            exchange_type=order_data.get("exchange_type", ExchangeType.PAPER),
            exchange_config=order_data.get("exchange_config", {})
        )

        # Add to database
        db.add(managed_order)
        db.commit()
        db.refresh(managed_order)

        # Prepare event data with exchange information
        event_data = {
            **order_data,
            "exchange_type": managed_order.exchange_type,
            "exchange_config": managed_order.exchange_config
        }

        # Dispatch order created event
        event = OrderEvent(
            event_type=OrderEventType.CREATED,
            order_id=managed_order.id,
            timestamp=datetime.utcnow(),
            data=event_data,
            chain_id=managed_order.chain_id,
            chain_type=managed_order.chain_type
        )
        OrderEventDispatcher.dispatch_event(event)

        # Convert to Pydantic model and return
        return ManagedOrder.model_validate(managed_order)

    @staticmethod
    async def create_order_chain(db: Session, user_id: int, chain_data: List[dict], chain_type: str, exchange_type: ExchangeType = ExchangeType.PAPER, exchange_config: Optional[dict] = None) -> List[ManagedOrder]:
        """Create a chain of related orders."""
        import uuid
        
        chain_id = str(uuid.uuid4())
        orders = []
        
        # Add exchange information to chain metadata
        chain_metadata = {
            "exchange_type": exchange_type,
            "exchange_config": exchange_config or {}
        }
        
        # Dispatch chain started event
        start_event = OrderEvent(
            event_type=OrderEventType.CHAIN_STARTED,
            order_id=0,
            timestamp=datetime.utcnow(),
            data={
                "chain_type": chain_type,
                **chain_metadata
            },
            chain_id=chain_id,
            chain_type=chain_type
        )
        OrderEventDispatcher.dispatch_event(start_event)
        
        try:
            for sequence, order_data in enumerate(chain_data):
                # Add chain and exchange information to each order
                order_data.update({
                    "chain_id": chain_id,
                    "chain_type": chain_type,
                    "chain_sequence": sequence,
                    "exchange_type": exchange_type,
                    "exchange_config": exchange_config
                })
                
                if sequence > 0:
                    order_data["parent_order_id"] = orders[-1].id
                
                # Create the order
                order = await OrderService.create_order(db, user_id, order_data)
                orders.append(order)
            
            # Dispatch chain completed event
            complete_event = OrderEvent(
                event_type=OrderEventType.CHAIN_COMPLETED,
                order_id=orders[-1].id,
                timestamp=datetime.utcnow(),
                data={
                    "orders": [order.id for order in orders],
                    **chain_metadata
                },
                chain_id=chain_id,
                chain_type=chain_type
            )
            OrderEventDispatcher.dispatch_event(complete_event)
            
        except Exception as e:
            # Dispatch chain failed event
            fail_event = OrderEvent(
                event_type=OrderEventType.CHAIN_FAILED,
                order_id=orders[-1].id if orders else 0,
                timestamp=datetime.utcnow(),
                data={
                    "error": str(e),
                    **chain_metadata
                },
                chain_id=chain_id,
                chain_type=chain_type
            )
            OrderEventDispatcher.dispatch_event(fail_event)
            raise
        
        return orders

    @staticmethod
    async def get_chain_orders(db: Session, chain_id: str, user_id: int) -> List[ManagedOrder]:
        """Get all orders in a specific chain."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError()

        orders = db.query(ManagedOrderDB).filter(
            ManagedOrderDB.chain_id == chain_id,
            ManagedOrderDB.owner_id == user_id
        ).order_by(ManagedOrderDB.chain_sequence).all()

        return [ManagedOrder.model_validate(order) for order in orders]

    @staticmethod
    async def update_chain_status(db: Session, chain_id: str, user_id: int, status: str, error: Optional[str] = None) -> List[ManagedOrder]:
        """Update the status of all orders in a chain."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError()

        orders = db.query(ManagedOrderDB).filter(
            ManagedOrderDB.chain_id == chain_id,
            ManagedOrderDB.owner_id == user_id
        ).all()

        for order in orders:
            order.chain_status = status
            if error:
                order.chain_error = error

        db.commit()
        return [ManagedOrder.model_validate(order) for order in orders]

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
