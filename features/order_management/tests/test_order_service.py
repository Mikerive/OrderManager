import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from features.order_management.service import OrderService
from features.order_management.models import ManagedOrderDB, OrderStatus, OrderPriority
from core.user.models import User
from core.exceptions import UnauthorizedError, OrderNotFoundError

@pytest.fixture
def test_user(test_db: Session):
    user = User(
        email="test@example.com",
        hashed_password="dummy_hash",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_order(test_db: Session, test_user):
    order = ManagedOrderDB(
        owner_id=test_user.id,
        title="Test Order",
        description="Test Description",
        status=OrderStatus.PENDING,
        priority=OrderPriority.MEDIUM,
        tags="test,order",
        estimated_hours=2.0,
        notes="Test notes"
    )
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)
    return order

@pytest.mark.asyncio
async def test_create_order(test_db: Session, test_user):
    order_data = {
        "title": "New Order",
        "description": "New Description",
        "priority": OrderPriority.HIGH,
        "tags": ["urgent", "important"],
        "estimated_hours": 3.0,
        "notes": "Important order"
    }
    
    order = await OrderService.create_order(test_db, test_user.id, order_data)
    assert order.title == "New Order"
    assert order.description == "New Description"
    assert order.priority == OrderPriority.HIGH
    assert order.tags == ["urgent", "important"]
    assert order.estimated_hours == 3.0
    assert order.notes == "Important order"
    assert order.owner_id == test_user.id

@pytest.mark.asyncio
async def test_get_order(test_db: Session, test_user, test_order):
    order = await OrderService.get_order(test_db, test_order.id, test_user.id)
    assert order.id == test_order.id
    assert order.title == test_order.title
    assert order.owner_id == test_user.id

@pytest.mark.asyncio
async def test_get_nonexistent_order(test_db: Session, test_user):
    with pytest.raises(OrderNotFoundError):
        await OrderService.get_order(test_db, 999, test_user.id)

@pytest.mark.asyncio
async def test_update_order(test_db: Session, test_user, test_order):
    update_data = {
        "title": "Updated Title",
        "priority": OrderPriority.HIGH,
        "tags": ["updated", "modified"]
    }
    
    updated_order = await OrderService.update_order(test_db, test_order.id, test_user.id, update_data)
    assert updated_order.title == "Updated Title"
    assert updated_order.priority == OrderPriority.HIGH
    assert updated_order.tags == ["updated", "modified"]

@pytest.mark.asyncio
async def test_delete_order(test_db: Session, test_user, test_order):
    await OrderService.delete_order(test_db, test_order.id, test_user.id)
    with pytest.raises(OrderNotFoundError):
        await OrderService.get_order(test_db, test_order.id, test_user.id)

@pytest.mark.asyncio
async def test_list_user_orders(test_db: Session, test_user, test_order):
    orders = await OrderService.list_user_orders(test_db, test_user.id)
    assert len(orders) > 0
    assert orders[0].id == test_order.id

@pytest.mark.asyncio
async def test_update_order_status(test_db: Session, test_user, test_order):
    updated_order = await OrderService.update_order_status(
        test_db, test_order.id, test_user.id, OrderStatus.IN_PROGRESS
    )
    assert updated_order.status == OrderStatus.IN_PROGRESS
    assert updated_order.started_at is not None

    completed_order = await OrderService.update_order_status(
        test_db, test_order.id, test_user.id, OrderStatus.COMPLETED
    )
    assert completed_order.status == OrderStatus.COMPLETED
    assert completed_order.completed_at is not None

@pytest.mark.asyncio
async def test_search_orders(test_db: Session, test_user, test_order):
    # Search by status
    orders = await OrderService.search_orders(
        test_db, user_id=test_user.id, status=OrderStatus.PENDING
    )
    assert len(orders) > 0
    assert orders[0].status == OrderStatus.PENDING

    # Search by priority
    orders = await OrderService.search_orders(
        test_db, user_id=test_user.id, priority=OrderPriority.MEDIUM
    )
    assert len(orders) > 0
    assert orders[0].priority == OrderPriority.MEDIUM

    # Search by tags
    orders = await OrderService.search_orders(
        test_db, user_id=test_user.id, tags=["test"]
    )
    assert len(orders) > 0
    assert "test" in orders[0].tags

    # Search by term
    orders = await OrderService.search_orders(
        test_db, user_id=test_user.id, search_term="Test"
    )
    assert len(orders) > 0
    assert "Test" in orders[0].title

@pytest.mark.asyncio
async def test_get_order_statistics(test_db: Session, test_user, test_order):
    stats = await OrderService.get_order_statistics(test_db, test_user.id)
    assert stats["total_orders"] > 0
    assert stats["status_counts"][OrderStatus.PENDING.value] > 0
    assert stats["priority_counts"][OrderPriority.MEDIUM.value] > 0

@pytest.mark.asyncio
async def test_unauthorized_access(test_db: Session):
    with pytest.raises(UnauthorizedError):
        await OrderService.get_order(test_db, 1, 999)  # Non-existent user

    with pytest.raises(UnauthorizedError):
        await OrderService.create_order(test_db, 999, {"title": "Test"})

    with pytest.raises(UnauthorizedError):
        await OrderService.update_order(test_db, 1, 999, {"title": "Test"})
