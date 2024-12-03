from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

from ...models import OrderCreate, OrderStatus, OrderType, OrderSide, OrderNode

class AlpacaEnvironment(str, Enum):
    PAPER = "paper"
    LIVE = "live"

class AlpacaCredentials(BaseModel):
    api_key: str
    api_secret: str
    environment: AlpacaEnvironment = AlpacaEnvironment.PAPER

class AlpacaOrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

    @classmethod
    def to_core_side(cls, side: "AlpacaOrderSide") -> OrderSide:
        return OrderSide(side.value)

    @classmethod
    def from_core_side(cls, side: OrderSide) -> "AlpacaOrderSide":
        return cls(side.value)

class AlpacaOrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"

    @classmethod
    def to_core_type(cls, order_type: "AlpacaOrderType") -> OrderType:
        return OrderType(order_type.value)

    @classmethod
    def from_core_type(cls, order_type: OrderType) -> "AlpacaOrderType":
        return cls(order_type.value)

class AlpacaTimeInForce(str, Enum):
    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"

class AlpacaTakeProfit(BaseModel):
    limit_price: float

class AlpacaStopLoss(BaseModel):
    stop_price: float
    limit_price: Optional[float] = None

class AlpacaOrderRequest(OrderNode):
    """Request model for placing orders with Alpaca."""
    time_in_force: AlpacaTimeInForce = AlpacaTimeInForce.DAY
    extended_hours: bool = False
    provider: str = "alpaca"

    @classmethod
    def from_core_order(cls, order: OrderCreate) -> "AlpacaOrderRequest":
        """Convert core order to Alpaca order request."""
        return cls(
            symbol=order.symbol,
            quantity=order.quantity,
            side=AlpacaOrderSide.from_core_side(order.side),
            type=AlpacaOrderType.from_core_type(order.order_type),
            limit_price=order.limit_price,
            stop_price=order.stop_price,
            trail_percent=order.trail_percent,
            trail_price=order.trail_price,
            additional_data=order.additional_data or {},
        )

    def to_core_order_create(self) -> OrderCreate:
        """Convert AlpacaOrderRequest to core OrderCreate."""
        return OrderCreate(
            id=0,  # Will be set by graph service
            title=self.title,
            description=self.description,
            order_type=self.order_type.value,
            side=self.side.value,
            symbol=self.symbol,
            quantity=self.quantity,
            provider="alpaca"
        )

class AlpacaOrder(OrderNode):
    """Alpaca order model extending core OrderNode."""
    exchange_order_id: str
    client_order_id: str
    asset_id: str
    asset_class: str
    notional: Optional[float] = None
    filled_avg_price: Optional[float] = None
    order_class: Optional[str] = None
    time_in_force: str
    extended_hours: bool
    legs: Optional[List["AlpacaOrder"]] = None
    provider: str = "alpaca"

    def to_core_order(self) -> OrderCreate:
        """Convert Alpaca order to core order."""
        return OrderCreate(
            provider_order_id=self.exchange_order_id,
            symbol=self.symbol,
            quantity=self.quantity,
            side=AlpacaOrderSide.to_core_side(AlpacaOrderSide(self.side)),
            order_type=AlpacaOrderType.to_core_type(AlpacaOrderType(self.type)),
            status=self.status,
            price=self.price,
            limit_price=self.limit_price,
            stop_price=self.stop_price,
            trail_percent=self.trail_percent,
            trail_price=self.trail_price,
            additional_data={
                "asset_id": self.asset_id,
                "asset_class": self.asset_class,
                "filled_avg_price": self.filled_avg_price,
                "order_class": self.order_class,
                "time_in_force": self.time_in_force,
                "extended_hours": self.extended_hours,
            }
        )

class AlpacaPosition(BaseModel):
    """Model for Alpaca position information."""
    symbol: str
    quantity: float
    asset_id: str
    exchange: str
    asset_class: str
    avg_entry_price: float
    side: str
    market_value: float
    unrealized_pl: float
    unrealized_plpc: float
    unrealized_intraday_pl: float
    unrealized_intraday_plpc: float
    current_price: float
    lastday_price: float
    change_today: float

class AlpacaAccount(BaseModel):
    """Model for Alpaca account information."""
    id: str
    account_number: str
    status: str
    currency: str
    cash: float
    portfolio_value: float
    pattern_day_trader: bool
    trading_blocked: bool
    transfers_blocked: bool
    account_blocked: bool
    created_at: str
    shorting_enabled: bool
    long_market_value: float
    short_market_value: float
    equity: float
    last_equity: float
    multiplier: float
    buying_power: float
    initial_margin: float
    maintenance_margin: float
    sma: Optional[float] = None
    daytrade_count: int
    last_maintenance_margin: float
    daytrading_buying_power: float
    regt_buying_power: float

class ConditionalOperator(str, Enum):
    GREATER_THAN = ">"
    LESS_THAN = "<"
    EQUAL_TO = "="

class ConditionalTriggerType(str, Enum):
    """Type of trigger for conditional orders."""
    TIME = "time"
    PRICE = "price"
    VOLUME = "volume"
    ANY = "any"
    ALL = "all"

class TimeCondition(BaseModel):
    timestamp: datetime
    operator: ConditionalOperator

class PriceCondition(BaseModel):
    symbol: str
    target_price: float
    operator: ConditionalOperator

class VolumeCondition(BaseModel):
    symbol: str
    target_volume: int
    operator: ConditionalOperator

class OrderCondition(BaseModel):
    trigger_type: ConditionalTriggerType
    condition: Union[TimeCondition, PriceCondition, VolumeCondition]

class ConditionalOrderRequest(AlpacaOrderRequest):
    """Request for placing a conditional order."""
    conditions: List[OrderCondition]
    trigger_type: ConditionalTriggerType = ConditionalTriggerType.ANY
    require_all: bool = False

class BracketOrderRequest(AlpacaOrderRequest):
    take_profit: AlpacaTakeProfit
    stop_loss: AlpacaStopLoss

class OCOOrderRequest(AlpacaOrderRequest):
    limit_price: float
    stop_price: float
    stop_limit_price: Optional[float] = None

class AlpacaOrderUpdate(BaseModel):
    qty: Optional[float] = None
    time_in_force: Optional[AlpacaTimeInForce] = None
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    trail: Optional[float] = None
    client_order_id: Optional[str] = None

class ChainedOrderRequest(BaseModel):
    """Request model for chained orders."""
    orders: List[Union[AlpacaOrderRequest, BracketOrderRequest, OCOOrderRequest, ConditionalOrderRequest]]
    require_all_fills: bool = True
    cancel_on_failure: bool = True

    def to_core_chain(self) -> List[OrderCreate]:
        """Convert chain request to list of core orders with dependencies."""
        core_orders = []
        
        for i, order in enumerate(self.orders):
            core_order = order.to_core_order_create()
            
            # Add dependency on previous order if not first order
            if i > 0:
                core_order.dependencies = [
                    OrderEdge(
                        from_order_id=i-1,
                        to_order_id=i,
                        condition_type="fill",
                        condition_data={}
                    )
                ]
            
            core_orders.append(core_order)
        
        return core_orders

def _map_to_core_order_type(alpaca_type: AlpacaOrderType) -> OrderType:
    """Map Alpaca order type to core order type."""
    mapping = {
        AlpacaOrderType.MARKET: OrderType.MARKET,
        AlpacaOrderType.LIMIT: OrderType.LIMIT,
        AlpacaOrderType.STOP: OrderType.STOP,
        AlpacaOrderType.STOP_LIMIT: OrderType.STOP_LIMIT,
        AlpacaOrderType.TRAILING_STOP: OrderType.TRAILING_STOP
    }
    return mapping[alpaca_type]

def _map_to_core_order_side(alpaca_side: AlpacaOrderSide) -> OrderSide:
    """Map Alpaca order side to core order side."""
    mapping = {
        AlpacaOrderSide.BUY: OrderSide.BUY,
        AlpacaOrderSide.SELL: OrderSide.SELL
    }
    return mapping[alpaca_side]

def map_alpaca_to_order_status(alpaca_status: str) -> OrderStatus:
    """Map Alpaca order status to core OrderStatus."""
    status_map = {
        "new": OrderStatus.PENDING,
        "accepted": OrderStatus.ACCEPTED,
        "rejected": OrderStatus.REJECTED,
        "filled": OrderStatus.FILLED,
        "partially_filled": OrderStatus.FILLED,
        "canceled": OrderStatus.CANCELLED,
        "expired": OrderStatus.EXPIRED,
        "replaced": OrderStatus.REPLACED,
        "pending_new": OrderStatus.PENDING,
        "pending_replace": OrderStatus.PENDING,
        "pending_cancel": OrderStatus.PENDING,
        "done_for_day": OrderStatus.COMPLETED,
        "stopped": OrderStatus.COMPLETED,
        "suspended": OrderStatus.CANCELLED,
        "calculated": OrderStatus.PENDING
    }
    return status_map.get(alpaca_status.lower(), OrderStatus.PENDING)
