from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from datetime import datetime

from core.database.database import get_db
from core.features.user.models import User
from .models import Order, OrderCreate, OrderUpdate

class OrderService:
    """Service class for handling order-related operations."""
    
    @staticmethod
    async def create_order(db: Session, order: OrderCreate, current_user: User) -> Order:
        """Create a new order."""
        db_order = Order(
            title=order.title,
            description=order.description,
            status=order.status,
            owner_id=current_user.id
        )
        
        try:
            db.add(db_order)
            db.commit()
            db.refresh(db_order)
            
            # Add dependencies if any
            if order.dependencies:
                await OrderService.update_dependencies(db, db_order.id, order.dependencies)
            
            return db_order
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Invalid order data")
    
    @staticmethod
    async def get_orders(
        db: Session,
        current_user: User,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """Get all orders for the current user."""
        return db.query(Order).filter(
            Order.owner_id == current_user.id
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    async def get_order(db: Session, order_id: int, current_user: User) -> Order:
        """Get a specific order."""
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.owner_id == current_user.id
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    
    @staticmethod
    async def update_order(
        db: Session,
        order_id: int,
        order_update: OrderUpdate,
        current_user: User
    ) -> Order:
        """Update an existing order."""
        db_order = await OrderService.get_order(db, order_id, current_user)
        
        update_data = order_update.dict(exclude_unset=True)
        dependencies = update_data.pop('dependencies', None)
        
        for field, value in update_data.items():
            setattr(db_order, field, value)
        
        db_order.updated_at = datetime.utcnow()
        
        if dependencies is not None:
            await OrderService.update_dependencies(db, order_id, dependencies)
        
        try:
            db.commit()
            db.refresh(db_order)
            return db_order
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Invalid order data")
    
    @staticmethod
    async def delete_order(db: Session, order_id: int, current_user: User) -> bool:
        """Delete an order."""
        db_order = await OrderService.get_order(db, order_id, current_user)
        
        try:
            db.delete(db_order)
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Cannot delete order with existing dependencies"
            )
    
    @staticmethod
    async def update_dependencies(
        db: Session,
        order_id: int,
        dependencies: List[int]
    ) -> None:
        """Update order dependencies."""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Clear existing dependencies
        order.dependencies = []
        
        # Add new dependencies
        for dep_id in dependencies:
            dep_order = db.query(Order).filter(Order.id == dep_id).first()
            if not dep_order:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dependency order {dep_id} not found"
                )
            order.dependencies.append(dep_order)
        
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Invalid dependency configuration"
            )
