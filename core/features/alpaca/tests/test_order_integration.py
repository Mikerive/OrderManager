import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from features.order_management.service import OrderService
from features.order_management.models import ExchangeType
from features.alpaca import initialize_alpaca
from core.orders.events import OrderEventDispatcher
from features.alpaca.models import AlpacaOrderCreate

@pytest.fixture
def mock_alpaca_service():
    """Create a mock Alpaca service."""
    with patch('features.alpaca.service.AlpacaService') as mock:
        service = mock.return_value
        service.place_order = Mock()
        service.place_bracket_order = Mock()
        service.place_oco_order = Mock()
        yield service

@pytest.fixture
def setup_alpaca(mock_alpaca_service):
    """Initialize Alpaca with mock service."""
    initialize_alpaca("test_key", "test_secret", True)
    return mock_alpaca_service

async def test_alpaca_order_placement(db, test_user, setup_alpaca):
    """Test that orders are properly routed to Alpaca."""
    mock_service = setup_alpaca
    
    # Create an order with Alpaca exchange
    order_data = {
        "title": "Buy AAPL",
        "symbol": "AAPL",
        "quantity": 100,
        "side": "buy",
        "order_type": "market",
        "exchange_type": ExchangeType.ALPACA,
        "exchange_config": {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "paper_trading": True
        }
    }
    
    order = await OrderService.create_order(db, test_user.id, order_data)
    
    # Verify Alpaca service was called
    mock_service.place_order.assert_called_once()
    placed_order = mock_service.place_order.call_args[0][0]
    assert isinstance(placed_order, AlpacaOrderCreate)
    assert placed_order.symbol == "AAPL"
    assert placed_order.qty == 100

async def test_alpaca_bracket_order(db, test_user, setup_alpaca):
    """Test that bracket orders are properly created in Alpaca."""
    mock_service = setup_alpaca
    
    # Create a bracket order chain
    chain_data = [
        {
            "title": "Entry",
            "symbol": "AAPL",
            "quantity": 100,
            "side": "buy",
            "order_type": "limit",
            "limit_price": 150.0
        }
    ]
    
    # Add take profit and stop loss to chain metadata
    chain_metadata = {
        "take_profit": {
            "limit_price": 160.0
        },
        "stop_loss": {
            "stop_price": 145.0,
            "limit_price": 144.0
        }
    }
    
    # Create the chain
    orders = await OrderService.create_order_chain(
        db,
        test_user.id,
        chain_data,
        "bracket",
        exchange_type=ExchangeType.ALPACA,
        exchange_config={
            "api_key": "test_key",
            "api_secret": "test_secret",
            "paper_trading": True
        }
    )
    
    # Verify bracket order was created
    mock_service.place_bracket_order.assert_called_once()
    args = mock_service.place_bracket_order.call_args[1]
    assert isinstance(args["entry_order"], AlpacaOrderCreate)
    assert args["take_profit_price"] == 160.0
    assert args["stop_loss_price"] == 145.0
    assert args["stop_loss_limit_price"] == 144.0

async def test_alpaca_oco_order(db, test_user, setup_alpaca):
    """Test that OCO orders are properly created in Alpaca."""
    mock_service = setup_alpaca
    
    # Create OCO order chain
    chain_data = [
        {
            "title": "Take Profit",
            "symbol": "AAPL",
            "quantity": 100,
            "side": "sell",
            "order_type": "limit",
            "limit_price": 160.0
        }
    ]
    
    # Add OCO leg to chain metadata
    chain_metadata = {
        "other_leg": {
            "symbol": "AAPL",
            "quantity": 100,
            "side": "sell",
            "order_type": "stop",
            "stop_price": 145.0
        }
    }
    
    # Create the chain
    orders = await OrderService.create_order_chain(
        db,
        test_user.id,
        chain_data,
        "oco",
        exchange_type=ExchangeType.ALPACA,
        exchange_config={
            "api_key": "test_key",
            "api_secret": "test_secret",
            "paper_trading": True
        }
    )
    
    # Verify OCO order was created
    mock_service.place_oco_order.assert_called_once()
    args = mock_service.place_oco_order.call_args[1]
    assert isinstance(args["first_order"], AlpacaOrderCreate)
    assert isinstance(args["second_order"], AlpacaOrderCreate)
    assert args["first_order"].limit_price == 160.0
    assert args["second_order"].stop_price == 145.0
