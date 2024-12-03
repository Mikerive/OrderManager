from typing import Optional, List, Union
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from ..models import OrderStatus, OrderType, OrderSide

class ExchangeOrderStatus(str, Enum):
    """Base exchange order status enum that can be mapped to core OrderStatus."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    ERROR = "error"

class BaseExchangeOrder(BaseModel):
    """Base model for exchange-specific orders."""
    exchange_order_id: str
    client_order_id: Optional[str] = None
    symbol: str
    quantity: float
    filled_quantity: float = 0
    remaining_quantity: float = 0
    price: Optional[float] = None
    status: ExchangeOrderStatus
    type: OrderType
    side: OrderSide
    created_at: datetime
    updated_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_core_status(self) -> OrderStatus:
        """Map exchange status to core OrderStatus."""
        raise NotImplementedError()

class BaseExchangePosition(BaseModel):
    """Base model for exchange positions."""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    side: OrderSide
    unrealized_pl: float
    market_value: float

class BaseExchangeAccount(BaseModel):
    """Base model for exchange account information."""
    account_id: str
    currency: str
    cash_balance: float
    portfolio_value: float
    buying_power: float
    status: str
