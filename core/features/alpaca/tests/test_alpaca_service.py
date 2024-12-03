import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import os
from dotenv import load_dotenv
from features.alpaca.service import AlpacaService
from features.alpaca.models import (
    AlpacaCredentials,
    AlpacaEnvironment,
    AlpacaOrderRequest,
    AlpacaOrderSide,
    AlpacaOrderType,
    AlpacaTimeInForce
)
from core.orders.models import OrderStatus, OrderCreate, OrderEdge
from core.orders.graph_service import OrderGraphService
from core.exceptions import UnauthorizedException, ValidationException
from core.user.models import User
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca.common.exceptions import APIError

# Fixtures
@pytest.fixture
def mock_order_service():
    return Mock()

@pytest.fixture
def mock_graph_service():
    return Mock(spec=OrderGraphService)

@pytest.fixture
def alpaca_service(mock_order_service, mock_graph_service):
    service = AlpacaService(order_service=mock_order_service, graph_service=mock_graph_service)
    service._trading_client = Mock()
    service._data_client = Mock()
    return service

@pytest.fixture
def mock_credentials():
    return AlpacaCredentials(
        api_key="test_key",
        api_secret="test_secret",
        environment=AlpacaEnvironment.PAPER
    )

@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="test_user",
        email="test@example.com"
    )

# Connection and Initialization Tests
@pytest.mark.asyncio
async def test_initialize_with_env_credentials():
    """Test that we can initialize with credentials from environment."""
    load_dotenv("features/alpaca/.env.example")
    
    # Get credentials from environment
    api_key = os.getenv("ALPACA_API_KEY")
    api_secret = os.getenv("ALPACA_API_SECRET")
    
    assert api_key is not None, "ALPACA_API_KEY not found in environment"
    assert api_secret is not None, "ALPACA_API_SECRET not found in environment"
    
    # Create service and initialize
    service = AlpacaService(Mock(), Mock(spec=OrderGraphService))
    with patch('alpaca.trading.client.TradingClient'), \
         patch('alpaca.data.historical.StockHistoricalDataClient'):
        await service.initialize(AlpacaCredentials(
            api_key=api_key,
            api_secret=api_secret,
            environment=AlpacaEnvironment.PAPER
        ))
        
        # Verify clients are initialized
        assert service._trading_client is not None
        assert service._data_client is not None

@pytest.mark.asyncio
async def test_initialize_success(alpaca_service, mock_credentials):
    """Test initialization with mock credentials."""
    with patch('alpaca.trading.client.TradingClient'), \
         patch('alpaca.data.historical.StockHistoricalDataClient'):
        await alpaca_service.initialize(mock_credentials)
        assert alpaca_service._trading_client is not None
        assert alpaca_service._data_client is not None

@pytest.mark.asyncio
async def test_initialize_failure(alpaca_service):
    """Test initialization with invalid credentials."""
    mock_error = APIError(401)
    mock_error.__str__ = lambda x: "401: Client Error: Unauthorized"
    
    with patch('features.alpaca.service.TradingClient', side_effect=mock_error), \
         patch('features.alpaca.service.StockHistoricalDataClient', side_effect=mock_error):
        with pytest.raises(UnauthorizedException) as exc_info:
            await alpaca_service.initialize(AlpacaCredentials(
                api_key="invalid",
                api_secret="invalid",
                environment=AlpacaEnvironment.PAPER
            ))
        assert "Failed to initialize" in str(exc_info.value)

# Basic Market Data Tests
@pytest.mark.asyncio
async def test_get_account_info(alpaca_service):
    """Test retrieving account information."""
    mock_account = Mock()
    mock_account._raw = {
        "id": "test_account",
        "account_number": "TEST123",
        "status": "ACTIVE",
        "currency": "USD",
        "cash": 25000.0,
        "portfolio_value": 100000.0,
        "pattern_day_trader": False,
        "trading_blocked": False,
        "transfers_blocked": False,
        "account_blocked": False,
        "created_at": "2024-01-01T00:00:00Z",
        "shorting_enabled": True,
        "long_market_value": 75000.0,
        "short_market_value": 0.0,
        "equity": 100000.0,
        "last_equity": 98000.0,
        "multiplier": 1.0,
        "buying_power": 50000.0,
        "initial_margin": 0.0,
        "maintenance_margin": 0.0,
        "daytrade_count": 0,
        "last_maintenance_margin": 0.0,
        "daytrading_buying_power": 200000.0,
        "regt_buying_power": 50000.0
    }
    alpaca_service._trading_client.get_account.return_value = mock_account
    
    result = await alpaca_service.get_account()
    assert result.status == "ACTIVE"
    assert result.equity == 100000.0
    assert result.buying_power == 50000.0

@pytest.mark.asyncio
async def test_get_positions(alpaca_service):
    """Test retrieving positions."""
    mock_position = Mock()
    mock_position._raw = {
        "asset_id": "test_asset_1",
        "symbol": "AAPL",
        "exchange": "NASDAQ",
        "asset_class": "us_equity",
        "avg_entry_price": 150.0,
        "qty": 100.0,
        "side": "long",
        "market_value": 16000.0,
        "cost_basis": 15000.0,
        "unrealized_pl": 1000.0,
        "unrealized_plpc": 0.0667,
        "unrealized_intraday_pl": 500.0,
        "unrealized_intraday_plpc": 0.0323,
        "current_price": 160.0,
        "lastday_price": 155.0,
        "change_today": 0.0323
    }
    alpaca_service._trading_client.get_all_positions.return_value = [mock_position]
    
    result = await alpaca_service.get_positions()
    assert len(result) == 1
    assert result[0].symbol == "AAPL"
    assert result[0].qty == 100.0
    assert result[0].market_value == 16000.0

@pytest.mark.asyncio
async def test_get_stock_quote(alpaca_service):
    """Test retrieving stock quotes."""
    mock_quote = Mock()
    mock_quote.ask_price = 150.0
    mock_quote.ask_size = 100
    mock_quote.bid_price = 149.5
    mock_quote.bid_size = 200
    mock_quote.timestamp = datetime.now()
    
    mock_quotes = {
        'AAPL': [mock_quote]
    }
    alpaca_service._data_client.get_stock_quotes.return_value = mock_quotes
    
    result = await alpaca_service.get_stock_quote("AAPL")
    assert result['symbol'] == 'AAPL'
    assert result['ask_price'] == 150.0
    assert result['bid_price'] == 149.5

# Basic Order Tests
@pytest.mark.asyncio
async def test_place_market_order(alpaca_service, mock_user):
    """Test placing a basic market order."""
    # Create order request
    order_request = AlpacaOrderRequest(
        symbol="AAPL",
        qty=10,
        side=AlpacaOrderSide.BUY,
        type=AlpacaOrderType.MARKET,
        time_in_force=AlpacaTimeInForce.DAY
    )
    
    # Mock graph service response
    mock_order = OrderCreate(
        id=1,
        title="BUY 10 AAPL",
        description="Market order for AAPL",
        order_type=order_request.type.value,
        side=order_request.side.value,
        symbol=order_request.symbol,
        quantity=order_request.qty,
        provider="alpaca"
    )
    alpaca_service.graph_service.create_order_chain.return_value = [mock_order]
    
    # Mock Alpaca API response
    mock_alpaca_order = Mock()
    mock_alpaca_order.id = "test_order_id"
    mock_alpaca_order.status = "accepted"
    mock_alpaca_order._raw = {
        'id': "test_order_id",
        'client_order_id': "test_client_id",
        'created_at': "2024-01-01T00:00:00Z",
        'asset_id': "test_asset",
        'symbol': "AAPL",
        'asset_class': "us_equity",
        'qty': 10,
        'order_type': "market",
        'type': "market",
        'side': "buy",
        'time_in_force': "day",
        'status': "accepted",
        'extended_hours': False
    }
    alpaca_service._trading_client.submit_order = AsyncMock(return_value=mock_alpaca_order)
    
    # Place order
    result = await alpaca_service.place_order(mock_user, order_request)
    
    # Verify order was created in graph
    alpaca_service.graph_service.create_order_chain.assert_called_once()
    
    # Verify order was submitted to Alpaca
    alpaca_service._trading_client.submit_order.assert_called_once_with(
        symbol="AAPL",
        qty=10,
        side="buy",
        type="market",
        time_in_force="day",
        extended_hours=False
    )

@pytest.mark.asyncio
async def test_cancel_order(alpaca_service):
    """Test canceling an order."""
    order_id = "test_order_id"
    await alpaca_service.cancel_order(order_id)
    alpaca_service._trading_client.cancel_order.assert_called_once_with(order_id)

@pytest.mark.asyncio
async def test_get_order_history(alpaca_service):
    """Test retrieving order history."""
    mock_order = Mock()
    mock_order._raw = {
        'id': "test_order_id",
        'client_order_id': "test_client_id",
        'created_at': "2024-01-01T00:00:00Z",
        'asset_id': "test_asset",
        'symbol': "AAPL",
        'asset_class': "us_equity",
        'qty': 100,
        'order_type': "market",
        'type': "market",
        'side': "buy",
        'time_in_force': "day",
        'status': "filled",
        'extended_hours': False
    }
    alpaca_service._trading_client.get_orders.return_value = [mock_order]
    
    result = await alpaca_service.get_order_history()
    assert len(result) == 1
    assert result[0].symbol == "AAPL"
    assert result[0].status == "filled"

# Error Handling Tests
@pytest.mark.asyncio
async def test_unauthorized_access(alpaca_service):
    """Test handling of unauthorized access."""
    alpaca_service._trading_client = None
    with pytest.raises(UnauthorizedException):
        await alpaca_service.get_account()

@pytest.mark.asyncio
async def test_api_error_handling(alpaca_service, mock_user):
    """Test handling of API errors."""
    mock_error = APIError(422)
    mock_error.__str__ = lambda x: "'Mock' object is not subscriptable"
    alpaca_service._trading_client.submit_order = AsyncMock(side_effect=mock_error)

    order_request = AlpacaOrderRequest(
        symbol="AAPL",
        qty=10,
        side=AlpacaOrderSide.BUY,
        type=AlpacaOrderType.MARKET,
        time_in_force=AlpacaTimeInForce.DAY
    )

    with pytest.raises(ValidationException) as exc_info:
        await alpaca_service.place_order(mock_user, order_request)
    assert str(exc_info.value) == "422: Failed to place order: 'Mock' object is not subscriptable"
