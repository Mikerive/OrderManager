import os
from datetime import datetime
from typing import List, Optional, Dict, Union
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockQuotesRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.common.exceptions import APIError

from ...models import OrderStatus, OrderType as CoreOrderType, OrderSide as CoreOrderSide, OrderCreate, OrderEdge
from ...service import OrderService
from ...graph_service import OrderGraphService
from core.exceptions import UnauthorizedException, ValidationException
from core.features.user.models import User

from .models import (
    AlpacaCredentials,
    AlpacaEnvironment,
    AlpacaOrder,
    AlpacaPosition,
    AlpacaAccount,
    AlpacaOrderRequest,
    AlpacaOrderUpdate,
    AlpacaOrderType,
    AlpacaOrderSide,
    AlpacaTimeInForce,
    map_alpaca_to_order_status,
    BracketOrderRequest,
    OCOOrderRequest,
    ConditionalTriggerType,
    ConditionalOperator,
    OrderCondition,
    ConditionalOrderRequest,
    ChainedOrderRequest
)

load_dotenv()

class AlpacaService:
    def __init__(self, order_service: OrderService, graph_service: OrderGraphService):
        self.order_service = order_service
        self.graph_service = graph_service
        self._trading_client = None
        self._data_client = None
        
    async def initialize(self, credentials: AlpacaCredentials) -> None:
        """Initialize Alpaca clients with credentials."""
        try:
            self._trading_client = TradingClient(
                api_key=credentials.api_key,
                secret_key=credentials.api_secret,
                paper=credentials.environment == AlpacaEnvironment.PAPER
            )
            
            self._data_client = StockHistoricalDataClient(
                api_key=credentials.api_key,
                secret_key=credentials.api_secret
            )
        except APIError as e:
            if e.status_code == 401:
                raise UnauthorizedException("Invalid Alpaca credentials")
            raise ValidationException(f"Failed to initialize Alpaca client: {str(e)}")
        except Exception as e:
            raise ValidationException(f"Failed to initialize Alpaca client: {str(e)}")

    def _check_auth(self):
        """Check if clients are initialized."""
        if not self._trading_client or not self._data_client:
            raise UnauthorizedException("Alpaca clients not initialized")

    async def get_account(self) -> AlpacaAccount:
        """Get Alpaca account information."""
        self._check_auth()
        try:
            account = self._trading_client.get_account()
            return AlpacaAccount(**account._raw)
        except APIError as e:
            if str(e).startswith("401"):
                raise UnauthorizedException("Unauthorized access to Alpaca API")
            raise ValidationException(f"Failed to get account info: {str(e)}")
        except Exception as e:
            raise ValidationException(f"Failed to get account info: {str(e)}")

    async def get_positions(self) -> List[AlpacaPosition]:
        """Get all open positions."""
        self._check_auth()
        try:
            positions = self._trading_client.get_all_positions()
            return [AlpacaPosition(**pos._raw) for pos in positions]
        except Exception as e:
            raise ValidationException(f"Failed to get positions: {str(e)}")

    async def place_order(
        self,
        user: User,
        order_request: AlpacaOrderRequest
    ) -> OrderCreate:
        """Place an order and create a corresponding order node."""
        self._check_auth()

        try:
            # Convert Alpaca order request to core order
            core_order = order_request.to_core_order_create()

            # Create order in graph
            created_order = self.graph_service.create_order_chain([core_order], user.id)[0]

            # Submit order to Alpaca
            order_params = {
                "symbol": order_request.symbol,
                "quantity": order_request.quantity,
                "side": order_request.side.value,
                "type": order_request.order_type.value,
                "time_in_force": order_request.time_in_force.value,
                "extended_hours": order_request.extended_hours
            }

            if order_request.order_type == AlpacaOrderType.LIMIT:
                if not order_request.limit_price:
                    raise ValidationException("Limit price required for limit orders")
                order_params["limit_price"] = order_request.limit_price

            if order_request.order_type == AlpacaOrderType.STOP:
                if not order_request.stop_price:
                    raise ValidationException("Stop price required for stop orders")
                order_params["stop_price"] = order_request.stop_price

            if order_request.order_type == AlpacaOrderType.TRAILING_STOP:
                if order_request.trail_percent:
                    order_params["trail_percent"] = order_request.trail_percent
                elif order_request.trail_price:
                    order_params["trail_price"] = order_request.trail_price
                else:
                    raise ValidationException("Either trail_percent or trail_price required for trailing stop orders")

            alpaca_order = await self._trading_client.submit_order(**order_params)

            # Update order with provider ID
            created_order.provider_order_id = alpaca_order.id
            created_order.status = map_alpaca_to_order_status(alpaca_order.status)
            self.graph_service.update_order_status(created_order.id, created_order.status)

            return created_order

        except Exception as e:
            raise ValidationException(f"Failed to place order: {str(e)}")

    async def place_bracket_order(
        self,
        user: User,
        order_request: BracketOrderRequest
    ) -> List[OrderCreate]:
        """Place a bracket order as a chain of orders."""
        self._check_auth()

        try:
            # Create entry order
            entry_order = order_request.to_core_order_create()

            # Create take profit order
            take_profit = OrderCreate(
                title=f"Take Profit {order_request.symbol}",
                description=f"Take profit order for {order_request.symbol}",
                order_type=CoreOrderType.LIMIT,
                side=CoreOrderSide.SELL if order_request.side == AlpacaOrderSide.BUY else CoreOrderSide.BUY,
                symbol=order_request.symbol,
                quantity=order_request.quantity,
                price=order_request.take_profit.limit_price,
                provider="alpaca",
                dependencies=[
                    OrderEdge(
                        from_order_id=0,
                        to_order_id=1,
                        condition_type="fill",
                        condition_data={}
                    )
                ]
            )

            # Create stop loss order
            stop_loss = OrderCreate(
                title=f"Stop Loss {order_request.symbol}",
                description=f"Stop loss order for {order_request.symbol}",
                order_type=CoreOrderType.STOP if not order_request.stop_loss.limit_price else CoreOrderType.STOP_LIMIT,
                side=CoreOrderSide.SELL if order_request.side == AlpacaOrderSide.BUY else CoreOrderSide.BUY,
                symbol=order_request.symbol,
                quantity=order_request.quantity,
                stop_price=order_request.stop_loss.stop_price,
                price=order_request.stop_loss.limit_price,
                provider="alpaca",
                dependencies=[
                    OrderEdge(
                        from_order_id=0,
                        to_order_id=2,
                        condition_type="fill",
                        condition_data={}
                    )
                ]
            )

            # Create order chain
            created_orders = self.graph_service.create_order_chain(
                [entry_order, take_profit, stop_loss],
                user.id
            )

            # Submit bracket order to Alpaca
            order_params = {
                "symbol": order_request.symbol,
                "quantity": order_request.quantity,
                "side": order_request.side.value,
                "type": order_request.type.value,
                "time_in_force": order_request.time_in_force.value,
                "take_profit": {"limit_price": order_request.take_profit.limit_price},
                "stop_loss": {
                    "stop_price": order_request.stop_loss.stop_price,
                    "limit_price": order_request.stop_loss.limit_price
                }
            }

            if order_request.type == AlpacaOrderType.LIMIT:
                order_params["limit_price"] = order_request.limit_price

            alpaca_order = self._trading_client.submit_order(**order_params)

            # Update orders with provider IDs and status
            for i, order in enumerate(created_orders):
                if i == 0:
                    order.provider_order_id = alpaca_order.id
                else:
                    order.provider_order_id = alpaca_order.legs[i-1].id
                order.status = map_alpaca_to_order_status(alpaca_order.status)
                self.graph_service.update_order_status(order.id, order.status)

            return created_orders

        except UnauthorizedException as e:
            raise e  # Re-raise UnauthorizedException without wrapping
        except Exception as e:
            raise ValidationException(f"Failed to place bracket order: {str(e)}")

    async def place_oco_order(
        self,
        user: User,
        order_request: OCOOrderRequest
    ) -> List[OrderCreate]:
        """Place an OCO (One-Cancels-Other) order as a chain of orders."""
        self._check_auth()

        try:
            # Create limit order
            limit_order = OrderCreate(
                title=f"Limit {order_request.symbol}",
                description=f"Limit order for {order_request.symbol}",
                order_type=CoreOrderType.LIMIT,
                side=order_request.side,
                symbol=order_request.symbol,
                quantity=order_request.quantity,
                price=order_request.limit_price,
                provider="alpaca"
            )

            # Create stop order
            stop_order = OrderCreate(
                title=f"Stop {order_request.symbol}",
                description=f"Stop order for {order_request.symbol}",
                order_type=CoreOrderType.STOP,
                side=order_request.side,
                symbol=order_request.symbol,
                quantity=order_request.quantity,
                stop_price=order_request.stop_price,
                provider="alpaca",
                dependencies=[
                    OrderEdge(
                        from_order_id=0,
                        to_order_id=1,
                        condition_type="cancel",
                        condition_data={}
                    )
                ]
            )

            # Create order chain
            created_orders = self.graph_service.create_order_chain(
                [limit_order, stop_order],
                user.id
            )

            # Submit OCO order to Alpaca
            order_params = {
                "symbol": order_request.symbol,
                "quantity": order_request.quantity,
                "side": order_request.side.value,
                "type": order_request.type.value,
                "time_in_force": order_request.time_in_force.value,
                "limit_price": order_request.limit_price,
                "stop_price": order_request.stop_price,
                "order_class": "oco"
            }

            alpaca_order = self._trading_client.submit_order(**order_params)

            # Update orders with provider IDs and status
            for i, order in enumerate(created_orders):
                if i == 0:
                    order.provider_order_id = alpaca_order.id
                else:
                    order.provider_order_id = alpaca_order.legs[i-1].id
                order.status = map_alpaca_to_order_status(alpaca_order.status)
                self.graph_service.update_order_status(order.id, order.status)

            return created_orders

        except Exception as e:
            raise ValidationException(f"Failed to place OCO order: {str(e)}")

    async def place_conditional_order(
        self,
        user: User,
        order_request: ConditionalOrderRequest
    ) -> OrderCreate:
        """Place a conditional order that executes when conditions are met."""
        self._check_auth()

        try:
            # Convert conditional order to core order
            core_order = order_request.to_core_order_create()

            # Add conditions as metadata
            core_order.additional_data = {
                "conditions": [
                    {
                        "trigger_type": condition.trigger_type.value,
                        "condition": condition.condition.dict()
                    }
                    for condition in order_request.conditions
                ],
                "require_all": order_request.require_all
            }

            # Create order in graph
            created_order = self.graph_service.create_order_chain([core_order], user.id)[0]

            # Start monitoring conditions
            # TODO: Implement condition monitoring service

            return created_order

        except Exception as e:
            raise ValidationException(f"Failed to place conditional order: {str(e)}")

    async def place_chained_orders(
        self,
        user: User,
        chain_request: ChainedOrderRequest
    ) -> List[OrderCreate]:
        """Place a chain of orders with dependencies."""
        self._check_auth()

        try:
            # Convert chain request to core orders
            core_orders = chain_request.to_core_chain()

            # Create order chain in graph
            created_orders = self.graph_service.create_order_chain(core_orders, user.id)

            # Submit first order to Alpaca
            first_order = chain_request.orders[0]
            alpaca_order = self.place_order(user, first_order)

            # Update first order with provider ID and status
            created_orders[0].provider_order_id = alpaca_order.id
            created_orders[0].status = map_alpaca_to_order_status(alpaca_order.status)
            self.graph_service.update_order_status(created_orders[0].id, created_orders[0].status)

            return created_orders

        except Exception as e:
            if chain_request.cancel_on_failure:
                # Cancel any orders that were created
                for order in created_orders:
                    await self.cancel_order(order.provider_order_id)
                    self.graph_service.cancel_dependent_orders(order.id)
            raise ValidationException(f"Failed to place chained orders: {str(e)}")

    async def get_order(self, order_id: str) -> AlpacaOrder:
        """Get a specific order by ID."""
        self._check_auth()
        try:
            order = self._trading_client.get_order(order_id)
            return AlpacaOrder(**order._raw)
        except Exception as e:
            raise ValidationException(f"Failed to get order: {str(e)}")

    async def update_order(
        self,
        order_id: str,
        update: AlpacaOrderUpdate
    ) -> AlpacaOrder:
        """Update an existing order."""
        self._check_auth()
        try:
            order = self._trading_client.replace_order(
                order_id=order_id,
                quantity=update.quantity,
                time_in_force=update.time_in_force.value if update.time_in_force else None,
                limit_price=update.limit_price,
                stop_price=update.stop_price,
                client_order_id=update.client_order_id
            )
            return AlpacaOrder(**order._raw)
        except Exception as e:
            raise ValidationException(f"Failed to update order: {str(e)}")

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        self._check_auth()
        try:
            self._trading_client.cancel_order(order_id)
            return True
        except Exception as e:
            raise ValidationException(f"Failed to cancel order: {str(e)}")

    async def get_stock_quote(self, symbol: str) -> Dict:
        """Get current quote for a stock."""
        self._check_auth()
        try:
            request = StockQuotesRequest(
                symbol_or_symbols=[symbol],
                limit=1
            )
            quotes = self._data_client.get_stock_quotes(request)

            if not quotes[symbol]:
                raise ValidationException(f"No quote available for {symbol}")

            latest_quote = quotes[symbol][0]
            return {
                'symbol': symbol,
                'ask_price': latest_quote.ask_price,
                'ask_size': latest_quote.ask_size,
                'bid_price': latest_quote.bid_price,
                'bid_size': latest_quote.bid_size,
                'timestamp': latest_quote.timestamp
            }
        except Exception as e:
            raise ValidationException(f"Failed to get stock quote: {str(e)}")

    async def sync_order_status(self, order: OrderCreate) -> None:
        """Sync order status with Alpaca."""
        try:
            if order.provider != "alpaca":
                return

            alpaca_order = self._trading_client.get_order_by_id(order.provider_order_id)
            order.status = map_alpaca_to_order_status(alpaca_order.status)
            await self.order_service.update_order_status(order.id, order.status)
        except Exception as e:
            print(f"Failed to sync order status: {str(e)}")

    async def get_order_history(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[AlpacaOrder]:
        """Get order history with optional filtering."""
        self._check_auth()
        try:
            request = GetOrdersRequest(
                status=status,
                limit=limit
            )
            orders = self._trading_client.get_orders(request)
            return [AlpacaOrder(**order._raw) for order in orders]
        except Exception as e:
            raise ValidationException(f"Failed to get order history: {str(e)}")

    async def get_portfolio_history(
        self,
        timeframe: TimeFrame = TimeFrame.Day,
        period: str = "1M"
    ) -> Dict:
        """Get portfolio history."""
        self._check_auth()
        try:
            history = self._trading_client.get_portfolio_history(
                timeframe=timeframe,
                period=period
            )
            return {
                "equity": history.equity,
                "profit_loss": history.profit_loss,
                "profit_loss_pct": history.profit_loss_pct,
                "base_value": history.base_value,
                "timeframe": timeframe,
                "period": period
            }
        except Exception as e:
            raise ValidationException(f"Failed to get portfolio history: {str(e)}")

    async def _evaluate_technical_indicator(
        self,
        symbol: str,
        indicator: ConditionalTriggerType,
        timeframe: str,
        period: int
    ) -> float:
        """Calculate technical indicator value."""
        try:
            bars_request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=timeframe,
                limit=period
            )
            bars = self._data_client.get_stock_bars(bars_request)

            if not bars[symbol]:
                raise ValidationException(f"No data available for {symbol}")

            prices = [bar.close for bar in bars[symbol]]

            if indicator == ConditionalTriggerType.MOVING_AVERAGE:
                return sum(prices) / len(prices)
            elif indicator == ConditionalTriggerType.RSI:
                gains = []
                losses = []
                for i in range(1, len(prices)):
                    change = prices[i] - prices[i-1]
                    if change >= 0:
                        gains.append(change)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(change))

                avg_gain = sum(gains) / len(gains)
                avg_loss = sum(losses) / len(losses)

                if avg_loss == 0:
                    return 100

                rs = avg_gain / avg_loss
                return 100 - (100 / (1 + rs))
            elif indicator == ConditionalTriggerType.VOLATILITY:
                mean = sum(prices) / len(prices)
                variance = sum((p - mean) ** 2 for p in prices) / len(prices)
                return (variance ** 0.5) / mean * 100  # Return as percentage
            elif indicator == ConditionalTriggerType.MACD:
                # Simple implementation - normally would use exponential moving average
                short_period = 12
                long_period = 26
                if len(prices) < long_period:
                    raise ValidationException(f"Not enough data for MACD calculation")

                short_ma = sum(prices[-short_period:]) / short_period
                long_ma = sum(prices[-long_period:]) / long_period
                return short_ma - long_ma

            raise ValidationException(f"Unsupported indicator: {indicator}")

        except Exception as e:
            raise ValidationException(f"Failed to calculate {indicator}: {str(e)}")

    async def _check_condition(
        self,
        condition: OrderCondition,
        symbol: str
    ) -> bool:
        """Check if a condition is met."""
        try:
            if condition.trigger_type == ConditionalTriggerType.TIME:
                current_time = datetime.now(timezone.utc)
                target_time = condition.condition.time

                if condition.condition.timezone != "UTC":
                    import pytz
                    tz = pytz.timezone(condition.condition.timezone)
                    current_time = current_time.astimezone(tz)
                    target_time = target_time.astimezone(tz)

                return self._compare_values(
                    current_time,
                    target_time,
                    condition.condition.operator
                )

            elif condition.trigger_type == ConditionalTriggerType.PRICE:
                quote = await self.get_stock_quote(
                    condition.condition.symbol or symbol
                )
                return self._compare_values(
                    quote['price'],
                    condition.condition.price,
                    condition.condition.operator
                )

            elif condition.trigger_type == ConditionalTriggerType.VOLUME:
                bars_request = StockBarsRequest(
                    symbol_or_symbols=[condition.condition.symbol or symbol],
                    timeframe=condition.condition.timeframe,
                    limit=1
                )
                bars = self._data_client.get_stock_bars(bars_request)
                volume = bars[condition.condition.symbol or symbol][0].volume

                return self._compare_values(
                    volume,
                    condition.condition.volume,
                    condition.condition.operator
                )

            else:  # Technical indicators
                value = await self._evaluate_technical_indicator(
                    symbol=condition.condition.symbol or symbol,
                    indicator=condition.condition.indicator,
                    timeframe=condition.condition.timeframe,
                    period=condition.condition.period
                )
                return self._compare_values(
                    value,
                    condition.condition.value,
                    condition.condition.operator
                )

        except Exception as e:
            raise ValidationException(f"Failed to check condition: {str(e)}")

    def _compare_values(
        self,
        value1: Union[float, int, datetime],
        value2: Union[float, int, datetime],
        operator: ConditionalOperator
    ) -> bool:
        """Compare two values using the specified operator."""
        if operator == ConditionalOperator.GREATER_THAN:
            return value1 > value2
        elif operator == ConditionalOperator.LESS_THAN:
            return value1 < value2
        elif operator == ConditionalOperator.GREATER_EQUAL:
            return value1 >= value2
        elif operator == ConditionalOperator.LESS_EQUAL:
            return value1 <= value2
        elif operator == ConditionalOperator.EQUAL:
            return value1 == value2
        elif operator == ConditionalOperator.NOT_EQUAL:
            return value1 != value2
        raise ValidationException(f"Invalid operator: {operator}")
