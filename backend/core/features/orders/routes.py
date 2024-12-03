from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from core.database.database import get_db
from features.user_management.auth import get_current_user
from features.user_management.models import User
from .models import OrderCreate, OrderUpdate, OrderResponse
from .service import OrderService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new order."""
    logger.info(f"CREATE ORDER ROUTE CALLED by user {current_user.email}")
    logger.debug(f"Order details: {order}")
    return await OrderService.create_order(db, order, current_user)

@router.get("/", response_model=List[OrderResponse])
async def read_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all orders for the current user."""
    logger.info(f"READ ORDERS ROUTE CALLED by user {current_user.email}")
    logger.debug(f"Skip: {skip}, Limit: {limit}")
    return await OrderService.get_orders(db, current_user, skip, limit)

@router.get("/{order_id}", response_model=OrderResponse)
async def read_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific order."""
    logger.info(f"READ ORDER ROUTE CALLED by user {current_user.email}")
    logger.debug(f"Order ID: {order_id}")
    return await OrderService.get_order(db, order_id, current_user)

@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing order."""
    logger.info(f"UPDATE ORDER ROUTE CALLED by user {current_user.email}")
    logger.debug(f"Order ID: {order_id}, Update Details: {order}")
    return await OrderService.update_order(db, order_id, order, current_user)

@router.delete("/{order_id}")
async def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an order."""
    logger.info(f"DELETE ORDER ROUTE CALLED by user {current_user.email}")
    logger.debug(f"Order ID: {order_id}")
    success = await OrderService.delete_order(db, order_id, current_user)
    if success:
        return {"message": "Order deleted successfully"}
    raise HTTPException(status_code=404, detail="Order not found or unauthorized")
