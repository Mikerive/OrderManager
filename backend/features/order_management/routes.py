from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_user
from core.user.model import User
from .models import (
    ManagedOrderCreate,
    ManagedOrderUpdate,
    ManagedOrderResponse,
    OrderStatus,
    OrderPriority
)
from .service import OrderManagementService

router = APIRouter(prefix="/api/order-management", tags=["order-management"])

@router.post("/orders/", response_model=ManagedOrderResponse)
async def create_managed_order(
    order: ManagedOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new managed order."""
    service = OrderManagementService(db)
    return service.create_order(current_user.id, order.dict())

@router.put("/orders/{order_id}/status", response_model=ManagedOrderResponse)
async def update_order_status(
    order_id: int,
    status: OrderStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the status of an order."""
    service = OrderManagementService(db)
    order = service.get_order(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to modify this order")
    
    return service.update_order_status(order_id, status)

@router.get("/orders/search", response_model=List[ManagedOrderResponse])
async def search_orders(
    status: Optional[OrderStatus] = None,
    priority: Optional[OrderPriority] = None,
    tags: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search orders with various filters."""
    service = OrderManagementService(db)
    
    # Only superusers can search other users' orders
    if user_id and user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to view other users' orders")
    
    # If not superuser and no user_id specified, show only own orders
    if not current_user.is_superuser and not user_id:
        user_id = current_user.id
    
    return service.search_orders(
        user_id=user_id,
        status=status,
        priority=priority,
        tags=tags,
        search_term=search
    )

@router.get("/orders/statistics")
async def get_order_statistics(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics about orders."""
    service = OrderManagementService(db)
    
    # Only superusers can view other users' statistics
    if user_id and user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to view other users' statistics")
    
    # If not superuser and no user_id specified, show only own statistics
    if not current_user.is_superuser and not user_id:
        user_id = current_user.id
    
    return service.get_order_statistics(user_id)
