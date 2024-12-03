import pytest
from datetime import datetime
from core.orders.events import (
    OrderEvent,
    OrderEventType,
    OrderEventListener,
    OrderEventDispatcher
)

class TestListener(OrderEventListener):
    """Test listener that records events for verification."""
    
    def __init__(self):
        self.events = []
        
    def on_order_created(self, event: OrderEvent) -> None:
        self.events.append(event)
        
    def on_chain_started(self, event: OrderEvent) -> None:
        self.events.append(event)
        
    def on_chain_completed(self, event: OrderEvent) -> None:
        self.events.append(event)

def test_event_dispatcher():
    """Test that events are properly dispatched to listeners."""
    # Create test listener
    listener = TestListener()
    
    # Register listener
    OrderEventDispatcher.register_listener(listener)
    
    # Create test event
    event = OrderEvent(
        event_type=OrderEventType.CREATED,
        order_id=1,
        timestamp=datetime.utcnow(),
        data={"symbol": "AAPL", "quantity": 100}
    )
    
    # Dispatch event
    OrderEventDispatcher.dispatch_event(event)
    
    # Verify event was received
    assert len(listener.events) == 1
    received_event = listener.events[0]
    assert received_event.event_type == OrderEventType.CREATED
    assert received_event.order_id == 1
    assert received_event.data["symbol"] == "AAPL"
    
    # Unregister listener
    OrderEventDispatcher.unregister_listener(listener)
    
    # Dispatch another event
    OrderEventDispatcher.dispatch_event(event)
    
    # Verify no new events were received
    assert len(listener.events) == 1

def test_chain_events():
    """Test chain-specific events."""
    listener = TestListener()
    OrderEventDispatcher.register_listener(listener)
    
    # Dispatch chain started event
    start_event = OrderEvent(
        event_type=OrderEventType.CHAIN_STARTED,
        order_id=0,
        timestamp=datetime.utcnow(),
        data={"chain_type": "bracket"},
        chain_id="test-chain",
        chain_type="bracket"
    )
    OrderEventDispatcher.dispatch_event(start_event)
    
    # Dispatch chain completed event
    complete_event = OrderEvent(
        event_type=OrderEventType.CHAIN_COMPLETED,
        order_id=1,
        timestamp=datetime.utcnow(),
        data={"orders": [1, 2, 3]},
        chain_id="test-chain",
        chain_type="bracket"
    )
    OrderEventDispatcher.dispatch_event(complete_event)
    
    # Verify events
    assert len(listener.events) == 2
    assert listener.events[0].event_type == OrderEventType.CHAIN_STARTED
    assert listener.events[1].event_type == OrderEventType.CHAIN_COMPLETED
    assert listener.events[0].chain_id == "test-chain"
    assert listener.events[1].chain_id == "test-chain"
