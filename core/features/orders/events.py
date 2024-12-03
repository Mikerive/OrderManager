from typing import Callable, Dict, List, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class OrderEventType(str, Enum):
    """Types of order events that can occur."""
    CREATED = "created"
    UPDATED = "updated"
    CANCELLED = "cancelled"
    FILLED = "filled"
    CHAIN_STARTED = "chain_started"
    CHAIN_COMPLETED = "chain_completed"
    CHAIN_FAILED = "chain_failed"

@dataclass
class OrderEvent:
    """Event data for order-related events."""
    event_type: OrderEventType
    order_id: int
    timestamp: datetime
    data: dict
    chain_id: str = None
    chain_type: str = None

class OrderEventListener:
    """Base class for order event listeners."""
    
    def on_order_created(self, event: OrderEvent) -> None:
        """Handle order creation events."""
        pass
        
    def on_order_updated(self, event: OrderEvent) -> None:
        """Handle order update events."""
        pass
        
    def on_order_cancelled(self, event: OrderEvent) -> None:
        """Handle order cancellation events."""
        pass
        
    def on_order_filled(self, event: OrderEvent) -> None:
        """Handle order fill events."""
        pass
        
    def on_chain_started(self, event: OrderEvent) -> None:
        """Handle chain start events."""
        pass
        
    def on_chain_completed(self, event: OrderEvent) -> None:
        """Handle chain completion events."""
        pass
        
    def on_chain_failed(self, event: OrderEvent) -> None:
        """Handle chain failure events."""
        pass

class OrderEventDispatcher:
    """Dispatches order events to registered listeners."""
    
    _instance = None
    _listeners: List[OrderEventListener] = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OrderEventDispatcher, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def register_listener(cls, listener: OrderEventListener) -> None:
        """Register a new event listener."""
        if listener not in cls._listeners:
            cls._listeners.append(listener)
    
    @classmethod
    def unregister_listener(cls, listener: OrderEventListener) -> None:
        """Unregister an event listener."""
        if listener in cls._listeners:
            cls._listeners.remove(listener)
    
    @classmethod
    def dispatch_event(cls, event: OrderEvent) -> None:
        """Dispatch an event to all registered listeners."""
        event_handler_map = {
            OrderEventType.CREATED: "on_order_created",
            OrderEventType.UPDATED: "on_order_updated",
            OrderEventType.CANCELLED: "on_order_cancelled",
            OrderEventType.FILLED: "on_order_filled",
            OrderEventType.CHAIN_STARTED: "on_chain_started",
            OrderEventType.CHAIN_COMPLETED: "on_chain_completed",
            OrderEventType.CHAIN_FAILED: "on_chain_failed"
        }
        
        handler_name = event_handler_map.get(event.event_type)
        if handler_name:
            for listener in cls._listeners:
                handler = getattr(listener, handler_name)
                handler(event)
