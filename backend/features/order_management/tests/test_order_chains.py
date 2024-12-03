import pytest
from sqlalchemy.orm import Session
from features.order_management.service import OrderService
from features.order_management.models import OrderStatus, OrderChainType
from core.exceptions import UnauthorizedError

async def test_create_order_chain(db: Session, test_user):
    """Test creating a chain of orders."""
    chain_data = [
        {
            "title": "Entry Order",
            "description": "Initial entry order",
            "status": OrderStatus.PENDING
        },
        {
            "title": "Take Profit",
            "description": "Take profit order",
            "status": OrderStatus.PENDING
        },
        {
            "title": "Stop Loss",
            "description": "Stop loss order",
            "status": OrderStatus.PENDING
        }
    ]

    # Create chain
    orders = await OrderService.create_order_chain(
        db, 
        test_user.id, 
        chain_data, 
        OrderChainType.BRACKET
    )

    # Verify chain was created correctly
    assert len(orders) == 3
    assert all(order.chain_id == orders[0].chain_id for order in orders)
    assert all(order.chain_type == OrderChainType.BRACKET for order in orders)
    
    # Verify sequence
    for i, order in enumerate(orders):
        assert order.chain_sequence == i
        if i > 0:
            assert order.parent_order_id == orders[i-1].id

async def test_get_chain_orders(db: Session, test_user):
    """Test retrieving all orders in a chain."""
    # Create a chain first
    chain_data = [
        {"title": "Order 1"},
        {"title": "Order 2"}
    ]
    created_orders = await OrderService.create_order_chain(
        db, 
        test_user.id, 
        chain_data, 
        OrderChainType.SEQUENTIAL
    )
    
    chain_id = created_orders[0].chain_id
    
    # Retrieve chain orders
    orders = await OrderService.get_chain_orders(db, chain_id, test_user.id)
    
    assert len(orders) == 2
    assert [order.title for order in orders] == ["Order 1", "Order 2"]
    assert all(order.chain_id == chain_id for order in orders)

async def test_update_chain_status(db: Session, test_user):
    """Test updating the status of all orders in a chain."""
    # Create a chain
    chain_data = [
        {"title": "Order 1"},
        {"title": "Order 2"}
    ]
    created_orders = await OrderService.create_order_chain(
        db, 
        test_user.id, 
        chain_data, 
        OrderChainType.SEQUENTIAL
    )
    
    chain_id = created_orders[0].chain_id
    
    # Update chain status
    updated_orders = await OrderService.update_chain_status(
        db,
        chain_id,
        test_user.id,
        "cancelled",
        "Chain cancelled by user"
    )
    
    assert all(order.chain_status == "cancelled" for order in updated_orders)
    assert all(order.chain_error == "Chain cancelled by user" for order in updated_orders)

async def test_unauthorized_chain_access(db: Session, test_user):
    """Test unauthorized access to chain operations."""
    chain_data = [{"title": "Order 1"}]
    
    # Create chain with valid user
    orders = await OrderService.create_order_chain(
        db, 
        test_user.id, 
        chain_data, 
        OrderChainType.SEQUENTIAL
    )
    
    chain_id = orders[0].chain_id
    
    # Try to access with invalid user
    invalid_user_id = test_user.id + 1
    
    with pytest.raises(UnauthorizedError):
        await OrderService.get_chain_orders(db, chain_id, invalid_user_id)
    
    with pytest.raises(UnauthorizedError):
        await OrderService.update_chain_status(
            db, 
            chain_id, 
            invalid_user_id, 
            "cancelled"
        )
