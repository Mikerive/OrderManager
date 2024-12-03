import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException

from core.models import User, Order
from core.testing import test_db, test_user
from ..service import OrderService
from ..models import OrderCreate, OrderUpdate

async def test_create_order(test_db: Session, test_user: User):
    """Test order creation service."""
    order_data = OrderCreate(
        title="Test Order",
        description="Test Description",
        status="pending"
    )
    
    order = await OrderService.create_order(test_db, order_data, test_user)
    assert order.title == "Test Order"
    assert order.description == "Test Description"
    assert order.status == "pending"
    assert order.owner_id == test_user.id

async def test_get_orders(test_db: Session, test_user: User):
    """Test getting all orders service."""
    # Create test orders
    orders = [
        Order(
            title=f"Order {i}",
            description=f"Description {i}",
            status="pending",
            owner_id=test_user.id
        )
        for i in range(3)
    ]
    for order in orders:
        test_db.add(order)
    test_db.commit()

    result = await OrderService.get_orders(test_db, test_user)
    assert len(result) == 3
    assert all(order.owner_id == test_user.id for order in result)

async def test_get_order(test_db: Session, test_user: User):
    """Test getting specific order service."""
    order = Order(
        title="Test Order",
        description="Test Description",
        status="pending",
        owner_id=test_user.id
    )
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)

    result = await OrderService.get_order(test_db, order.id, test_user)
    assert result.title == "Test Order"
    assert result.owner_id == test_user.id

async def test_get_nonexistent_order(test_db: Session, test_user: User):
    """Test getting non-existent order raises exception."""
    with pytest.raises(HTTPException) as exc_info:
        await OrderService.get_order(test_db, 999, test_user)
    assert exc_info.value.status_code == 404

async def test_update_order(test_db: Session, test_user: User):
    """Test updating order service."""
    order = Order(
        title="Original Title",
        description="Original Description",
        status="pending",
        owner_id=test_user.id
    )
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)

    update_data = OrderUpdate(
        title="Updated Title",
        description="Updated Description",
        status="active"
    )
    
    updated_order = await OrderService.update_order(
        test_db,
        order.id,
        update_data,
        test_user
    )
    assert updated_order.title == "Updated Title"
    assert updated_order.description == "Updated Description"
    assert updated_order.status == "active"

async def test_delete_order(test_db: Session, test_user: User):
    """Test deleting order service."""
    order = Order(
        title="Test Order",
        description="Test Description",
        status="pending",
        owner_id=test_user.id
    )
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)

    success = await OrderService.delete_order(test_db, order.id, test_user)
    assert success is True
    assert test_db.query(Order).filter(Order.id == order.id).first() is None

async def test_update_dependencies(test_db: Session, test_user: User):
    """Test updating order dependencies."""
    # Create orders
    orders = [
        Order(
            title=f"Order {i}",
            description=f"Description {i}",
            status="pending",
            owner_id=test_user.id
        )
        for i in range(3)
    ]
    for order in orders:
        test_db.add(order)
    test_db.commit()
    for order in orders:
        test_db.refresh(order)

    # Update dependencies
    await OrderService.update_dependencies(
        test_db,
        orders[2].id,
        [orders[0].id, orders[1].id]
    )

    # Verify dependencies
    order = test_db.query(Order).filter(Order.id == orders[2].id).first()
    assert len(order.dependencies) == 2
    assert orders[0] in order.dependencies
    assert orders[1] in order.dependencies
