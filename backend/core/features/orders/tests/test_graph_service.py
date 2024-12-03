import pytest
from datetime import datetime, timezone
from unittest.mock import Mock
from sqlalchemy.orm import Session
from core.orders.graph_service import OrderGraphService
from core.orders.models import (
    Order,
    OrderCreate,
    OrderEdge,
    OrderType,
    OrderSide,
    OrderStatus
)
from core.user.models import User

@pytest.fixture
def db_session():
    """Mock database session"""
    return Mock(spec=Session)

@pytest.fixture
def graph_service(db_session):
    return OrderGraphService(db_session)

@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="test_user",
        email="test@example.com"
    )

@pytest.fixture
def sample_orders():
    """Create sample orders for testing"""
    return [
        OrderCreate(
            title="Buy AAPL Stop",
            description="Initial stop buy order",
            order_type=OrderType.STOP,
            side=OrderSide.BUY,
            symbol="AAPL",
            quantity=100,
            stop_price=150.0,
            provider="alpaca",
            dependencies=[]
        ),
        OrderCreate(
            title="Sell AAPL Limit",
            description="Take profit order",
            order_type=OrderType.LIMIT,
            side=OrderSide.SELL,
            symbol="AAPL",
            quantity=100,
            price=160.0,
            provider="alpaca",
            dependencies=[
                OrderEdge(
                    from_order_id=0,
                    to_order_id=1,
                    condition_type="fill",
                    condition_data={}
                )
            ]
        ),
        OrderCreate(
            title="Sell AAPL Trail",
            description="Trailing stop order",
            order_type=OrderType.TRAILING_STOP,
            side=OrderSide.SELL,
            symbol="AAPL",
            quantity=100,
            trail_percent=1.0,
            provider="alpaca",
            dependencies=[
                OrderEdge(
                    from_order_id=1,
                    to_order_id=2,
                    condition_type="fill",
                    condition_data={}
                )
            ]
        )
    ]

def test_create_order_chain(graph_service, db_session, mock_user, sample_orders):
    # Mock the database operations
    created_orders = []
    for i, order in enumerate(sample_orders):
        mock_order = Order(
            id=i+1,
            title=order.title,
            description=order.description,
            status=OrderStatus.PENDING,
            order_type=order.order_type.value,
            side=order.side.value,
            symbol=order.symbol,
            quantity=order.quantity,
            price=order.price,
            stop_price=order.stop_price,
            trail_percent=order.trail_percent,
            provider=order.provider,
            owner_id=mock_user.id,
            created_at=datetime.now(timezone.utc)
        )
        created_orders.append(mock_order)
    
    db_session.add.side_effect = lambda x: None
    db_session.flush.side_effect = lambda: None
    db_session.commit.side_effect = lambda: None
    
    # Test creating the order chain
    result = graph_service.create_order_chain(sample_orders, mock_user.id)
    
    # Verify the results
    assert len(result) == 3
    assert db_session.add.call_count == 3
    assert db_session.commit.call_count == 1
    
    # Verify dependencies were created
    db_session.execute.assert_called()  # Dependencies were added

def test_get_ready_orders(graph_service, db_session, mock_user):
    # Mock query results
    mock_orders = [
        Order(
            id=1,
            title="Ready Order",
            status=OrderStatus.PENDING,
            order_type=OrderType.MARKET.value,
            side=OrderSide.BUY.value,
            symbol="AAPL",
            quantity=100,
            owner_id=mock_user.id
        )
    ]
    
    # Setup mock query chain
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = mock_orders
    db_session.query.return_value = mock_query
    
    # Test getting ready orders
    result = graph_service.get_ready_orders(mock_user.id)
    
    # Verify results
    assert len(result) == 1
    assert result[0].title == "Ready Order"
    assert result[0].status == OrderStatus.PENDING

def test_update_order_status(graph_service, db_session):
    # Create mock order
    mock_order = Order(
        id=1,
        title="Test Order",
        status=OrderStatus.PENDING,
        order_type=OrderType.MARKET.value,
        side=OrderSide.BUY.value,
        symbol="AAPL",
        quantity=100
    )
    
    # Setup mock query
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_order
    db_session.query.return_value = mock_query
    
    # Test updating order status
    result = graph_service.update_order_status(1, OrderStatus.FILLED)
    
    # Verify results
    assert result.status == OrderStatus.FILLED
    assert db_session.commit.called
    
    # Verify dependent orders were checked
    db_session.query.assert_called()

def test_cancel_dependent_orders(graph_service, db_session):
    # Create mock orders
    mock_orders = [
        Order(
            id=2,
            title="Dependent Order",
            status=OrderStatus.PENDING,
            order_type=OrderType.MARKET.value,
            side=OrderSide.SELL.value,
            symbol="AAPL",
            quantity=100
        )
    ]
    
    # Setup mock queries
    mock_query = Mock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [(2,)]  # Return dependent order IDs
    db_session.query.return_value = mock_query
    
    # Mock getting individual orders
    def mock_get_order(Order):
        return mock_query
    db_session.query.side_effect = mock_get_order
    mock_query.first.return_value = mock_orders[0]
    
    # Test cancelling dependent orders
    result = graph_service.cancel_dependent_orders(1)
    
    # Verify results
    assert len(result) == 1
    assert result[0].status == OrderStatus.CANCELLED
    assert db_session.commit.called

def test_get_order_chain(graph_service, db_session):
    # Mock edge data
    mock_edges = [
        (1, 2, "fill", {"condition": "test"}),
        (2, 3, "fill", {"condition": "test"})
    ]
    
    # Setup mock query
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = mock_edges
    db_session.query.return_value = mock_query
    
    # Test getting order chain
    result = graph_service.get_order_chain(1)
    
    # Verify results
    assert 1 in result
    assert isinstance(result[1], list)
    assert len(result[1]) == 1  # One edge from order 1
