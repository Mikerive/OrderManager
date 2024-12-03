import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from features.order_management.service import OrderService
from features.order_management.models import (
    OrderStatus,
    ExchangeType,
    ExchangeConfig,
    OrderPriority
)
from core.orders.events import OrderEventDispatcher, OrderEventListener, OrderEvent

class TestExchangeListener(OrderEventListener):
    """Test listener that records exchange-related events."""
    
    def __init__(self):
        self.events = []
        
    def on_order_created(self, event: OrderEvent) -> None:
        if "exchange_type" in event.data:
            self.events.append(event)

async def test_create_alpaca_order(db: Session, test_user):
    """Test creating an order with Alpaca exchange configuration."""
    # Setup test listener
    listener = TestExchangeListener()
    OrderEventDispatcher.register_listener(listener)
    
    # Create order with Alpaca config
    order_data = {
        "title": "Buy AAPL",
        "symbol": "AAPL",
        "quantity": 100,
        "side": "buy",
        "order_type": "market",
        "exchange_type": ExchangeType.ALPACA,
        "exchange_config": {
            "exchange_type": ExchangeType.ALPACA,
            "api_key": "test_key",
            "api_secret": "test_secret",
            "paper_trading": True
        }
    }
    
    order = await OrderService.create_order(db, test_user.id, order_data)
    
    # Verify order was created with correct exchange info
    assert order.exchange_type == ExchangeType.ALPACA
    assert order.exchange_config.api_key == "test_key"
    assert order.exchange_config.paper_trading is True
    
    # Verify event was dispatched with exchange info
    assert len(listener.events) == 1
    event = listener.events[0]
    assert event.data["exchange_type"] == ExchangeType.ALPACA
    assert event.data["exchange_config"]["api_key"] == "test_key"

async def test_create_exchange_order_chain(db: Session, test_user):
    """Test creating a chain of orders with exchange configuration."""
    chain_data = [
        {
            "title": "Entry Order",
            "symbol": "AAPL",
            "quantity": 100,
            "side": "buy",
            "order_type": "limit",
            "limit_price": 150.0
        },
        {
            "title": "Take Profit",
            "symbol": "AAPL",
            "quantity": 100,
            "side": "sell",
            "order_type": "limit",
            "limit_price": 160.0
        }
    ]
    
    exchange_config = {
        "exchange_type": ExchangeType.ALPACA,
        "api_key": "test_key",
        "api_secret": "test_secret",
        "paper_trading": True
    }
    
    # Create chain with exchange config
    orders = await OrderService.create_order_chain(
        db,
        test_user.id,
        chain_data,
        "bracket",
        exchange_type=ExchangeType.ALPACA,
        exchange_config=exchange_config
    )
    
    # Verify all orders in chain have correct exchange config
    assert len(orders) == 2
    for order in orders:
        assert order.exchange_type == ExchangeType.ALPACA
        assert order.exchange_config.api_key == "test_key"
        assert order.exchange_config.paper_trading is True

async def test_paper_trading_order(db: Session, test_user):
    """Test creating a paper trading order."""
    order_data = {
        "title": "Paper Trade",
        "symbol": "TSLA",
        "quantity": 10,
        "side": "buy",
        "order_type": "market",
        "exchange_type": ExchangeType.PAPER,
        "exchange_config": {
            "exchange_type": ExchangeType.PAPER,
            "paper_trading": True
        }
    }
    
    order = await OrderService.create_order(db, test_user.id, order_data)
    
    # Verify paper trading configuration
    assert order.exchange_type == ExchangeType.PAPER
    assert order.exchange_config.paper_trading is True
    assert order.status == OrderStatus.PENDING
