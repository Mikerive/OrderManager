import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta
from features.alpaca.service import AlpacaService
from features.alpaca.models import (
    ConditionalOrderRequest,
    ChainedOrderRequest,
    OrderCondition,
    TimeCondition,
    PriceCondition,
    VolumeCondition,
    ConditionalTriggerType,
    ConditionalOperator,
    AlpacaOrderSide,
    AlpacaOrderType,
    AlpacaOrderRequest,
    BracketOrderRequest,
    OCOOrderRequest,
    AlpacaTakeProfit,
    AlpacaStopLoss
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
    return Mock(spec=OrderGraphService)

@pytest.fixture
def alpaca_service(mock_order_service, mock_graph_service):
    service = AlpacaService(order_service=mock_order_service, graph_service=mock_graph_service)
    service._trading_client = Mock()
    service._data_client = Mock()
    return service

@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="test_user",
        email="test@example.com"
    )

@pytest.mark.asyncio
async def test_place_conditional_order_with_time_condition(alpaca_service, mock_user):
    # Mock order response
    mock_order = Mock(
        id="order_id",
        status="accepted",
        symbol="AAPL",
        qty="100",
        side="buy",
        type="market"
    )
    alpaca_service._trading_client.submit_order.return_value = mock_order

    # Create time-based conditional order
    future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    order_request = ConditionalOrderRequest(
        symbol="AAPL",
        qty=100,
        side=AlpacaOrderSide.BUY,
        type=AlpacaOrderType.MARKET,
        conditions=[
            OrderCondition(
                trigger_type=ConditionalTriggerType.TIME,
                condition=TimeCondition(
                    timestamp=future_time,
                    operator=ConditionalOperator.GREATER_THAN
                )
            )
        ],
        trigger_type=ConditionalTriggerType.ANY
    )

    # Mock graph service response
    mock_core_order = OrderCreate(
        title="AAPL TIME_CONDITION",
        order_type=OrderType.MARKET,
        side=OrderSide.BUY,
        symbol="AAPL",
        quantity=100,
        provider="alpaca"
    )
    alpaca_service.graph_service.create_order_chain.return_value = [mock_core_order]

    # Execute test
    result = await alpaca_service.place_conditional_order(mock_user, order_request)
    assert result.status == "submitted"


@pytest.mark.asyncio
async def test_place_conditional_order_with_price_condition(alpaca_service, mock_user):
    # Setup price condition
    order_request = ConditionalOrderRequest(
        symbol="AAPL",
        qty=10,
        side=AlpacaOrderSide.BUY,
        type=AlpacaOrderType.MARKET,
        conditions=[
            OrderCondition(
                trigger_type=ConditionalTriggerType.PRICE,
                condition=PriceCondition(
                    symbol="AAPL",
                    target_price=150.0,
                    operator=ConditionalOperator.GREATER_THAN
                )
            )
        ],
        trigger_type=ConditionalTriggerType.ANY
    )

    # Mock graph service response
    mock_core_order = OrderCreate(
        title="AAPL PRICE_CONDITION",
        order_type=OrderType.MARKET,
        side=OrderSide.BUY,
        symbol="AAPL",
        quantity=10,
        provider="alpaca"
    )
    alpaca_service.graph_service.create_order_chain.return_value = [mock_core_order]

    # Execute test
    result = await alpaca_service.place_conditional_order(mock_user, order_request)
    assert result.status == "submitted"


@pytest.mark.asyncio
async def test_place_conditional_order_with_volume_condition(alpaca_service, mock_user):
    # Setup volume condition
    order_request = ConditionalOrderRequest(
        symbol="AAPL",
        qty=10,
        side=AlpacaOrderSide.BUY,
        type=AlpacaOrderType.MARKET,
        conditions=[
            OrderCondition(
                trigger_type=ConditionalTriggerType.VOLUME,
                condition=VolumeCondition(
                    symbol="AAPL",
                    target_volume=1000000,
                    operator=ConditionalOperator.GREATER_THAN
                )
            )
        ],
        trigger_type=ConditionalTriggerType.ANY
    )

    # Mock graph service response
    mock_core_order = OrderCreate(
        title="AAPL VOLUME_CONDITION",
        order_type=OrderType.MARKET,
        side=OrderSide.BUY,
        symbol="AAPL",
        quantity=10,
        provider="alpaca"
    )
    alpaca_service.graph_service.create_order_chain.return_value = [mock_core_order]

    # Execute test
    result = await alpaca_service.place_conditional_order(mock_user, order_request)
    assert result.status == "submitted"


@pytest.mark.asyncio
async def test_place_chained_orders(alpaca_service, mock_user):
    # Mock order responses
    mock_orders = [
        Mock(
            id=f"order_id_{i}",
            status="filled" if i == 0 else "accepted",
            symbol="AAPL",
            qty="100",
            side="buy",
            type="market"
        ) for i in range(2)
    ]
    alpaca_service._trading_client.submit_order.side_effect = mock_orders

    # Create chain request with stop buy -> bracket order -> trailing stop
    chain_request = ChainedOrderRequest(
        orders=[
            # 1. Initial Stop Buy
            AlpacaOrderRequest(
                symbol="AAPL",
                qty=100,
                side=AlpacaOrderSide.BUY,
                type=AlpacaOrderType.STOP,
                stop_price=150.0
            ),
            # 2. Bracket Order
            BracketOrderRequest(
                symbol="AAPL",
                qty=100,
                side=AlpacaOrderSide.SELL,
                type=AlpacaOrderType.LIMIT,
                limit_price=160.0,
                take_profit=AlpacaTakeProfit(limit_price=165.0),
                stop_loss=AlpacaStopLoss(stop_price=145.0)
            )
        ],
        require_all_fills=True,
        cancel_on_failure=True
    )

    # Mock graph service response
    mock_core_orders = [
        OrderCreate(
            title=f"Order {i}",
            order_type=OrderType.MARKET,
            side=OrderSide.BUY,
            symbol="AAPL",
            quantity=100,
            provider="alpaca",
            provider_order_id=f"order_id_{i}"
        ) for i in range(2)
    ]
    alpaca_service.graph_service.create_order_chain.return_value = mock_core_orders

    # Execute test
    result = await alpaca_service.place_chained_orders(mock_user, chain_request)
    assert len(result) == 2
    assert all(order.status == OrderStatus.ACCEPTED for order in result)


@pytest.mark.asyncio
async def test_chain_cancellation_on_failure(alpaca_service, mock_user):
    # Mock first order to fail
    mock_failed_order = Mock(
        id="order_id_1",
        status="rejected",
        symbol="AAPL",
        qty="100",
        side="buy",
        type="market"
    )
    alpaca_service._trading_client.submit_order.side_effect = ValidationException("Order rejected")

    # Create chain request
    chain_request = ChainedOrderRequest(
        orders=[
            AlpacaOrderRequest(
                symbol="AAPL",
                qty=100,
                side=AlpacaOrderSide.BUY,
                type=AlpacaOrderType.MARKET
            ),
            AlpacaOrderRequest(
                symbol="AAPL",
                qty=100,
                side=AlpacaOrderSide.SELL,
                type=AlpacaOrderType.LIMIT,
                limit_price=160.0
            )
        ],
        require_all_fills=True,
        cancel_on_failure=True
    )

    # Mock graph service
    mock_core_orders = [
        OrderCreate(
            title=f"Order {i}",
            order_type=OrderType.MARKET,
            side=OrderSide.BUY,
            symbol="AAPL",
            quantity=100,
            provider="alpaca",
            provider_order_id=f"order_id_{i}"
        ) for i in range(2)
    ]
    alpaca_service.graph_service.create_order_chain.return_value = mock_core_orders

    # Execute test
    with pytest.raises(ValidationException):
        await alpaca_service.place_chained_orders(mock_user, chain_request)
