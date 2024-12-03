import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
from features.alpaca.service import AlpacaService
from features.alpaca.models import (
    AlpacaOrderRequest,
    BracketOrderRequest,
    OCOOrderRequest,
    AlpacaTakeProfit,
    AlpacaStopLoss,
    AlpacaOrderSide,
    AlpacaOrderType,
    AlpacaTimeInForce
)
from core.orders.models import (
    OrderStatus,
    OrderType,
    OrderSide,
    OrderEdge,
    OrderCreate
)
from core.user.models import User
from core.orders.graph_service import OrderGraphService
from core.exceptions import ValidationException, UnauthorizedException


@pytest.fixture
def mock_order_service():
    return Mock()

@pytest.fixture
def mock_graph_service():
    mock = MagicMock(spec=OrderGraphService)
    mock.create_order = MagicMock()
    mock.create_order_chain = MagicMock()
    mock.update_order_status = MagicMock()
    return mock

@pytest.fixture
def alpaca_service(mock_order_service, mock_graph_service):
    service = AlpacaService(order_service=mock_order_service, graph_service=mock_graph_service)
    service._trading_client = MagicMock()
    service._data_client = MagicMock()
    return service

@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="test_user",
        email="test@example.com"
    )


@pytest.mark.asyncio
async def test_place_bracket_order(alpaca_service, mock_user):
    # Mock order response
    mock_legs = [
        MagicMock(
            id=f"leg_id_{i}",
            status="accepted",
            symbol="AAPL",
            qty="100"
        ) for i in range(2)
    ]
    mock_order = MagicMock(
        id="order_id",
        status="accepted",
        symbol="AAPL",
        qty="100",
        side="buy",
        type="market",
        legs=mock_legs
    )
    alpaca_service._trading_client.submit_order.return_value = mock_order

    # Create bracket order request
    order_request = BracketOrderRequest(
        symbol="AAPL",
        qty=100,
        side=AlpacaOrderSide.BUY,
        type=AlpacaOrderType.MARKET,
        time_in_force=AlpacaTimeInForce.DAY,
        take_profit=AlpacaTakeProfit(limit_price=160.0),
        stop_loss=AlpacaStopLoss(stop_price=140.0, limit_price=139.0)
    )

    # Mock graph service response
    mock_core_orders = [
        OrderCreate(
            id=i,
            title=f"AAPL {order_type}",
            description=f"{order_type} order for AAPL",
            order_type=order_type,
            side=side,
            symbol="AAPL",
            quantity=100,
            provider="alpaca",
            provider_order_id="order_id" if i == 0 else f"leg_id_{i-1}",
            price=price,
            stop_price=stop_price
        ) for i, (order_type, side, price, stop_price) in enumerate([
            (OrderType.MARKET, OrderSide.BUY, None, None),
            (OrderType.LIMIT, OrderSide.SELL, 160.0, None),
            (OrderType.STOP_LIMIT, OrderSide.SELL, 139.0, 140.0)
        ])
    ]
    alpaca_service.graph_service.create_order_chain.return_value = mock_core_orders

    # Place order
    created_orders = await alpaca_service.place_bracket_order(mock_user, order_request)

    # Verify order submission
    alpaca_service._trading_client.submit_order.assert_called_once_with(
        symbol="AAPL",
        qty=100,
        side="buy",
        type="market",
        time_in_force="day",
        take_profit={"limit_price": 160.0},
        stop_loss={"stop_price": 140.0, "limit_price": 139.0}
    )

    # Verify graph service calls
    alpaca_service.graph_service.create_order_chain.assert_called_once()
    chain_request = alpaca_service.graph_service.create_order_chain.call_args[0][0]
    
    # Verify entry order
    assert chain_request[0].symbol == "AAPL"
    assert chain_request[0].quantity == 100
    assert chain_request[0].order_type == OrderType.MARKET
    assert chain_request[0].side == OrderSide.BUY
    
    # Verify take profit order
    assert chain_request[1].order_type == OrderType.LIMIT
    assert chain_request[1].side == OrderSide.SELL
    assert chain_request[1].price == 160.0
    assert len(chain_request[1].dependencies) == 1
    assert chain_request[1].dependencies[0].condition_type == "fill"
    
    # Verify stop loss order
    assert chain_request[2].order_type == OrderType.STOP_LIMIT
    assert chain_request[2].side == OrderSide.SELL
    assert chain_request[2].stop_price == 140.0
    assert chain_request[2].price == 139.0
    assert len(chain_request[2].dependencies) == 1
    assert chain_request[2].dependencies[0].condition_type == "fill"

    # Verify order updates
    assert created_orders[0].provider_order_id == "order_id"
    assert created_orders[1].provider_order_id == "leg_id_0"
    assert created_orders[2].provider_order_id == "leg_id_1"


@pytest.mark.asyncio
async def test_place_oco_order(alpaca_service, mock_user):
    # Mock order response
    mock_legs = [
        MagicMock(
            id=f"leg_id_{i}",
            status="accepted",
            symbol="AAPL",
            qty="100"
        ) for i in range(1)
    ]
    mock_order = MagicMock(
        id="order_id",
        status="accepted",
        symbol="AAPL",
        qty="100",
        side="buy",
        type="limit",
        legs=mock_legs
    )
    alpaca_service._trading_client.submit_order.return_value = mock_order

    # Create OCO order request
    order_request = OCOOrderRequest(
        symbol="AAPL",
        qty=100,
        side=AlpacaOrderSide.BUY,
        type=AlpacaOrderType.LIMIT,
        time_in_force=AlpacaTimeInForce.DAY,
        limit_price=150.0,
        stop_price=140.0
    )

    # Mock graph service response
    mock_core_orders = [
        OrderCreate(
            id=i,
            title=f"AAPL {order_type}",
            description=f"{order_type} order for AAPL",
            order_type=order_type,
            side=OrderSide.BUY,
            symbol="AAPL",
            quantity=100,
            provider="alpaca",
            provider_order_id="order_id" if i == 0 else f"leg_id_{i-1}",
            price=price,
            stop_price=stop_price
        ) for i, (order_type, price, stop_price) in enumerate([
            (OrderType.LIMIT, 150.0, None),
            (OrderType.STOP, None, 140.0)
        ])
    ]
    alpaca_service.graph_service.create_order_chain.return_value = mock_core_orders

    # Place order
    created_orders = await alpaca_service.place_oco_order(mock_user, order_request)

    # Verify order submission
    alpaca_service._trading_client.submit_order.assert_called_once_with(
        symbol="AAPL",
        qty=100,
        side="buy",
        type="limit",
        time_in_force="day",
        limit_price=150.0,
        stop_price=140.0,
        order_class="oco"
    )

    # Verify graph service calls
    alpaca_service.graph_service.create_order_chain.assert_called_once()
    chain_request = alpaca_service.graph_service.create_order_chain.call_args[0][0]
    
    # Verify limit order
    assert chain_request[0].symbol == "AAPL"
    assert chain_request[0].quantity == 100
    assert chain_request[0].order_type == OrderType.LIMIT
    assert chain_request[0].side == OrderSide.BUY
    assert chain_request[0].price == 150.0
    assert not chain_request[0].dependencies
    
    # Verify stop order
    assert chain_request[1].order_type == OrderType.STOP
    assert chain_request[1].side == OrderSide.BUY
    assert chain_request[1].stop_price == 140.0
    assert len(chain_request[1].dependencies) == 1
    assert chain_request[1].dependencies[0].condition_type == "cancel"
    assert chain_request[1].dependencies[0].from_order_id == 0
    assert chain_request[1].dependencies[0].to_order_id == 1

    # Verify order updates
    assert created_orders[0].provider_order_id == "order_id"
    assert created_orders[1].provider_order_id == "leg_id_0"


@pytest.mark.asyncio
async def test_bracket_order_rejection(alpaca_service, mock_user):
    # Mock order rejection
    alpaca_service._trading_client.submit_order.side_effect = ValidationException("Invalid bracket order")

    # Create bracket order request
    order_request = BracketOrderRequest(
        symbol="AAPL",
        qty=100,
        side=AlpacaOrderSide.BUY,
        type=AlpacaOrderType.MARKET,
        take_profit=AlpacaTakeProfit(limit_price=160.0),
        stop_loss=AlpacaStopLoss(stop_price=140.0)
    )

    # Execute test
    with pytest.raises(ValidationException) as exc_info:
        await alpaca_service.place_bracket_order(mock_user, order_request)
    assert "Invalid bracket order" in str(exc_info.value)


@pytest.mark.asyncio
async def test_oco_order_invalid_prices(alpaca_service, mock_user):
    # Create OCO order with invalid prices (stop price higher than limit)
    order_request = OCOOrderRequest(
        symbol="AAPL",
        qty=100,
        side=AlpacaOrderSide.SELL,
        type=AlpacaOrderType.LIMIT,
        limit_price=140.0,  # Lower than stop price
        stop_price=160.0    # Higher than limit price
    )

    # Mock validation error
    alpaca_service._trading_client.submit_order.side_effect = ValidationException("Invalid OCO order prices")

    # Execute test
    with pytest.raises(ValidationException) as exc_info:
        await alpaca_service.place_oco_order(mock_user, order_request)
    assert "Invalid OCO order prices" in str(exc_info.value)


@pytest.mark.asyncio
async def test_bracket_order_take_profit_validation(alpaca_service, mock_user):
    # Create bracket order with take profit below entry
    order_request = BracketOrderRequest(
        symbol="AAPL",
        qty=100,
        side=AlpacaOrderSide.BUY,
        type=AlpacaOrderType.LIMIT,
        limit_price=150.0,
        take_profit=AlpacaTakeProfit(limit_price=140.0),  # Below entry price for buy order
        stop_loss=AlpacaStopLoss(stop_price=130.0)
    )

    # Mock validation error
    alpaca_service._trading_client.submit_order.side_effect = ValidationException("Take profit price must be above entry price for buy orders")

    # Execute test
    with pytest.raises(ValidationException) as exc_info:
        await alpaca_service.place_bracket_order(mock_user, order_request)
    assert "Take profit price must be above entry price for buy orders" in str(exc_info.value)


@pytest.mark.asyncio
async def test_unauthorized_bracket_order(alpaca_service, mock_user):
    # Mock unauthorized error
    alpaca_service._trading_client.submit_order.side_effect = UnauthorizedException("Invalid credentials")

    # Create bracket order request
    order_request = BracketOrderRequest(
        symbol="AAPL",
        qty=100,
        side=AlpacaOrderSide.BUY,
        type=AlpacaOrderType.MARKET,
        take_profit=AlpacaTakeProfit(limit_price=160.0),
        stop_loss=AlpacaStopLoss(stop_price=140.0)
    )

    # Execute test
    with pytest.raises(UnauthorizedException) as exc_info:
        await alpaca_service.place_bracket_order(mock_user, order_request)
    assert "Invalid credentials" in str(exc_info.value)
