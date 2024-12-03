import os
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from dotenv import load_dotenv

from core.features.orders.exchanges.alpaca.service import AlpacaService
from core.features.orders.exchanges.alpaca.models import (
    AlpacaCredentials, AlpacaEnvironment, AlpacaOrderRequest,
    AlpacaOrderSide, AlpacaOrderType, AlpacaTimeInForce
)
from core.features.orders.models import OrderCreate, OrderType, OrderSide
from core.features.orders.service import OrderService
from core.features.orders.graph_service import OrderGraphService
from core.exceptions import UnauthorizedException, ValidationException
from core.features.user.models import User
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide as AlpacaOrderSideEnum, OrderType as AlpacaOrderTypeEnum, TimeInForce as AlpacaTimeInForceEnum
from alpaca.common.exceptions import APIError

# Fixtures
@pytest.fixture
def mock_order_service():
    return Mock(spec=OrderService)

@pytest.fixture
def mock_graph_service():
    return Mock(spec=OrderGraphService)

@pytest.fixture
def alpaca_service(mock_order_service, mock_graph_service):
    service = AlpacaService(mock_order_service, mock_graph_service)
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
    user = User(
        id=1,
        email="test@example.com",
        username="test_user"
    )
    return user

# Connection and Initialization Tests
@pytest.mark.asyncio
async def test_initialize_with_env_credentials():
    """Test that we can initialize with credentials from environment."""
    # Mock environment variables
    env_vars = {
        "ALPACA_API_KEY": "test_key",
        "ALPACA_API_SECRET": "test_secret",
        "ALPACA_ENVIRONMENT": "paper"
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        service = AlpacaService(Mock(), Mock())
        await service.initialize(AlpacaCredentials(
            api_key="test_key",
            api_secret="test_secret",
            environment=AlpacaEnvironment.PAPER
        ))
        assert service._trading_client is not None
        assert service._data_client is not None

@pytest.mark.asyncio
async def test_initialize_success(alpaca_service, mock_credentials):
    """Test initialization with mock credentials."""
    await alpaca_service.initialize(mock_credentials)
    assert alpaca_service._trading_client is not None
    assert alpaca_service._data_client is not None

@pytest.mark.asyncio
async def test_initialize_failure(alpaca_service):
    """Test initialization with invalid credentials."""
    class MockAPIError(APIError):
        @property
        def status_code(self):
            return 401
        
        def __str__(self):
            return "401: Client Error: Unauthorized"
    
    mock_error = MockAPIError(401)
    
    with patch('alpaca.trading.client.TradingClient.__init__', side_effect=mock_error), \
         patch('alpaca.data.historical.StockHistoricalDataClient.__init__', side_effect=mock_error):
        with pytest.raises(UnauthorizedException):
            await alpaca_service.initialize(AlpacaCredentials(
                api_key="invalid",
                api_secret="invalid",
                environment=AlpacaEnvironment.PAPER
            ))

# Basic Market Data Tests
@pytest.mark.asyncio
async def test_get_account_info(alpaca_service):
    """Test retrieving account information."""
    mock_account = {
        'id': "test_account",
        'account_number': "123456789",
        'status': "ACTIVE",
        'currency': "USD",
        'cash': 100000.0,
        'portfolio_value': 150000.0,
        'pattern_day_trader': False,
        'trading_blocked': False,
        'transfers_blocked': False,
        'account_blocked': False,
        'created_at': "2024-01-01T00:00:00Z",
        'shorting_enabled': True,
        'long_market_value': 50000.0,
        'short_market_value': 0.0,
        'equity': 150000.0,
        'last_equity': 145000.0,
        'multiplier': 1.0,
        'buying_power': 200000.0,
        'initial_margin': 75000.0,
        'maintenance_margin': 50000.0,
        'daytrade_count': 0,
        'last_maintenance_margin': 48000.0,
        'daytrading_buying_power': 300000.0,
        'regt_buying_power': 200000.0
    }
    alpaca_service._trading_client.get_account.return_value._raw = mock_account
    
    result = await alpaca_service.get_account()
    assert result.id == "test_account"
    assert result.account_number == "123456789"
    assert result.status == "ACTIVE"
    assert result.portfolio_value == 150000.0

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
        "quantity": 100.0,
        "side": "long",
        "market_value": 16000.0,
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
    assert result[0].quantity == 100.0

@pytest.mark.asyncio
async def test_get_stock_quote(alpaca_service):
    """Test retrieving stock quotes."""
    mock_quote = Mock()
    mock_quote.ask_price = 160.50
    mock_quote.ask_size = 100
    mock_quote.bid_price = 160.25
    mock_quote.bid_size = 200
    mock_quote.timestamp = "2024-01-01T00:00:00Z"
    
    mock_quotes = {
        "AAPL": [mock_quote]
    }
    alpaca_service._data_client.get_stock_quotes.return_value = mock_quotes

    result = await alpaca_service.get_stock_quote("AAPL")
    
    assert result == {
        'symbol': 'AAPL',
        'ask_price': 160.50,
        'ask_size': 100,
        'bid_price': 160.25,
        'bid_size': 200,
        'timestamp': '2024-01-01T00:00:00Z'
    }

# Basic Order Tests
@pytest.mark.asyncio
async def test_place_market_order(alpaca_service, mock_user):
    """Test placing a basic market order."""
    # Create order request
    order_request = AlpacaOrderRequest(
        title="Buy AAPL",
        description="Market order to buy AAPL",
        symbol="AAPL",
        quantity=10,
        side=AlpacaOrderSide.BUY,
        order_type=AlpacaOrderType.MARKET,
        time_in_force=AlpacaTimeInForce.DAY
    )

    # Mock graph service response
    mock_order = OrderCreate(
        id=1,
        title="Buy AAPL",
        description="Market order to buy AAPL",
        order_type=order_request.order_type.value,
        side=order_request.side.value,
        symbol=order_request.symbol,
        quantity=order_request.quantity,
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
        'quantity': 10,
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
        quantity=10,
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
        'exchange_order_id': "test_order_id",
        'client_order_id': "test_client_id",
        'created_at': "2024-01-01T00:00:00Z",
        'asset_id': "test_asset",
        'symbol': "AAPL",
        'asset_class': "us_equity",
        'title': "Buy AAPL",
        'description': "Market order to buy AAPL",
        'quantity': 100,
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
    assert result[0].exchange_order_id == "test_order_id"
    assert result[0].symbol == "AAPL"
    assert result[0].quantity == 100

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
    class MockAPIError(APIError):
        @property
        def status_code(self):
            return 422
        
        def __str__(self):
            return "422: Invalid order parameters"
    
    mock_error = MockAPIError(422)
    
    # Mock graph service response
    mock_order = OrderCreate(
        id=1,
        title="Buy AAPL",
        description="Market order to buy AAPL",
        order_type="market",
        side="buy",
        symbol="AAPL",
        quantity=10,
        provider="alpaca"
    )
    alpaca_service.graph_service.create_order_chain.return_value = [mock_order]
    
    # Mock Alpaca API error
    alpaca_service._trading_client.submit_order = AsyncMock(side_effect=mock_error)

    order_request = AlpacaOrderRequest(
        title="Buy AAPL",
        description="Market order to buy AAPL",
        symbol="AAPL",
        quantity=10,
        side=AlpacaOrderSide.BUY,
        order_type=AlpacaOrderType.MARKET,
        time_in_force=AlpacaTimeInForce.DAY
    )

    with pytest.raises(ValidationException) as exc_info:
        await alpaca_service.place_order(mock_user, order_request)
    assert str(exc_info.value) == "422: Failed to place order: 422: Invalid order parameters"
