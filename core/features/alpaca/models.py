from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

from core.orders.models import OrderCreate, OrderStatus, OrderType as CoreOrderType, OrderSide as CoreOrderSide, OrderEdge

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

class AlpacaOrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"

class AlpacaTimeInForce(str, Enum):
    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"

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

class AlpacaTakeProfit(BaseModel):
    limit_price: float

class AlpacaStopLoss(BaseModel):
    stop_price: float
    limit_price: Optional[float] = None

class AlpacaOrderRequest(BaseModel):
    symbol: str
    qty: float
    side: AlpacaOrderSide
    type: AlpacaOrderType
    time_in_force: AlpacaTimeInForce = AlpacaTimeInForce.DAY
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    trail_percent: Optional[float] = None
    trail_price: Optional[float] = None
    extended_hours: bool = False

    def to_core_order_create(self) -> OrderCreate:
        """Convert to core OrderCreate model."""
        return OrderCreate(
            title=f"{self.side.value.upper()} {self.qty} {self.symbol}",
            description=f"Alpaca {self.type.value} order for {self.symbol}",
            order_type=_map_to_core_order_type(self.type),
            side=_map_to_core_order_side(self.side),
            symbol=self.symbol,
            quantity=self.qty,
            price=self.limit_price,
            stop_price=self.stop_price,
            provider="alpaca",
            additional_data={
                "time_in_force": self.time_in_force.value,
                "extended_hours": self.extended_hours,
                "trail_percent": self.trail_percent,
                "trail_price": self.trail_price
            }
        )

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

class AlpacaOrder(BaseModel):
    id: str
    client_order_id: str
    created_at: str
    updated_at: Optional[str] = None
    submitted_at: Optional[str] = None
    filled_at: Optional[str] = None
    expired_at: Optional[str] = None
    canceled_at: Optional[str] = None
    failed_at: Optional[str] = None
    replaced_at: Optional[str] = None
    replaced_by: Optional[str] = None
    replaces: Optional[str] = None
    asset_id: str
    symbol: str
    asset_class: str
    notional: Optional[float] = None
    qty: Optional[float] = None
    filled_qty: Optional[float] = None
    filled_avg_price: Optional[float] = None
    order_class: Optional[str] = None
    order_type: str
    type: str
    side: str
    time_in_force: str
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str
    extended_hours: bool
    legs: Optional[List["AlpacaOrder"]] = None
    trail_percent: Optional[float] = None
    trail_price: Optional[float] = None
    hwm: Optional[float] = None

class AlpacaPosition(BaseModel):
    asset_id: str
    symbol: str
    exchange: str
    asset_class: str
    avg_entry_price: float
    qty: float
    side: str
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    unrealized_intraday_pl: float
    unrealized_intraday_plpc: float
    current_price: float
    lastday_price: float
    change_today: float

class AlpacaAccount(BaseModel):
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

def _map_to_core_order_type(alpaca_type: AlpacaOrderType) -> CoreOrderType:
    """Map Alpaca order type to core order type."""
    mapping = {
        AlpacaOrderType.MARKET: CoreOrderType.MARKET,
        AlpacaOrderType.LIMIT: CoreOrderType.LIMIT,
        AlpacaOrderType.STOP: CoreOrderType.STOP,
        AlpacaOrderType.STOP_LIMIT: CoreOrderType.STOP_LIMIT,
        AlpacaOrderType.TRAILING_STOP: CoreOrderType.TRAILING_STOP
    }
    return mapping[alpaca_type]

def _map_to_core_order_side(alpaca_side: AlpacaOrderSide) -> CoreOrderSide:
    """Map Alpaca order side to core order side."""
    mapping = {
        AlpacaOrderSide.BUY: CoreOrderSide.BUY,
        AlpacaOrderSide.SELL: CoreOrderSide.SELL
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
