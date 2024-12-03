from typing import Optional
from core.orders.events import OrderEventListener, OrderEvent, OrderEventType
from features.alpaca.service import AlpacaService
from features.alpaca.models import AlpacaOrderCreate
from features.order_management.models import ExchangeType

class AlpacaOrderListener(OrderEventListener):
    """Listens for order events and handles communication with Alpaca."""
    
    def __init__(self, alpaca_service: AlpacaService):
        self.alpaca_service = alpaca_service
    
    def on_order_created(self, event: OrderEvent) -> None:
        """Handle order creation by submitting to Alpaca."""
        # Only handle Alpaca orders
        if event.data.get("exchange_type") != ExchangeType.ALPACA:
            return

        order_data = event.data
        
        try:
            # Create Alpaca order
            alpaca_order = AlpacaOrderCreate(
                symbol=order_data["symbol"],
                qty=order_data["quantity"],
                side=order_data["side"],
                type=order_data["order_type"],
                time_in_force=order_data.get("time_in_force", "day"),
                limit_price=order_data.get("limit_price"),
                stop_price=order_data.get("stop_price"),
                trail_price=order_data.get("trail_price"),
                trail_percent=order_data.get("trail_percent"),
                extended_hours=order_data.get("extended_hours", False),
                client_order_id=str(event.order_id)
            )
            
            # Handle different order types based on chain type
            if event.chain_id and event.chain_type:
                if event.chain_type == "bracket":
                    self._handle_bracket_order(event, alpaca_order)
                elif event.chain_type == "oco":
                    self._handle_oco_order(event, alpaca_order)
                else:
                    # For sequential chains or single orders, place normally
                    self.alpaca_service.place_order(alpaca_order)
            else:
                # Single order
                self.alpaca_service.place_order(alpaca_order)
                
        except Exception as e:
            # Dispatch order failed event
            fail_event = OrderEvent(
                event_type=OrderEventType.FAILED,
                order_id=event.order_id,
                timestamp=event.timestamp,
                data={"error": str(e), **order_data},
                chain_id=event.chain_id,
                chain_type=event.chain_type
            )
            OrderEventDispatcher.dispatch_event(fail_event)
            raise
    
    def on_order_cancelled(self, event: OrderEvent) -> None:
        """Handle order cancellation in Alpaca."""
        if event.data.get("exchange_type") != ExchangeType.ALPACA:
            return
            
        try:
            self.alpaca_service.cancel_order(str(event.order_id))
        except Exception as e:
            # Log error but don't raise since order might already be cancelled
            print(f"Error cancelling order {event.order_id}: {str(e)}")
    
    def _handle_bracket_order(self, event: OrderEvent, entry_order: AlpacaOrderCreate) -> None:
        """Handle bracket order creation in Alpaca."""
        order_data = event.data
        
        # Get take profit and stop loss parameters from chain metadata
        chain_metadata = order_data.get("chain_metadata", {})
        take_profit = chain_metadata.get("take_profit", {})
        stop_loss = chain_metadata.get("stop_loss", {})
        
        self.alpaca_service.place_bracket_order(
            entry_order=entry_order,
            take_profit_price=take_profit.get("limit_price"),
            stop_loss_price=stop_loss.get("stop_price"),
            take_profit_limit_price=take_profit.get("limit_price"),
            stop_loss_limit_price=stop_loss.get("limit_price")
        )
    
    def _handle_oco_order(self, event: OrderEvent, first_order: AlpacaOrderCreate) -> None:
        """Handle OCO (One-Cancels-Other) order creation in Alpaca."""
        order_data = event.data
        chain_metadata = order_data.get("chain_metadata", {})
        other_leg = chain_metadata.get("other_leg", {})
        
        self.alpaca_service.place_oco_order(
            first_order=first_order,
            second_order=AlpacaOrderCreate(
                symbol=other_leg["symbol"],
                qty=other_leg["quantity"],
                side=other_leg["side"],
                type=other_leg["order_type"],
                time_in_force=other_leg.get("time_in_force", "day"),
                limit_price=other_leg.get("limit_price"),
                stop_price=other_leg.get("stop_price")
            )
        )
