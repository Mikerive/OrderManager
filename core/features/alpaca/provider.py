from typing import List
from core.features import ExchangeProvider
from .service import AlpacaService

class AlpacaExchangeProvider(ExchangeProvider):
    """Alpaca implementation of exchange provider."""
    
    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        self.service = AlpacaService(api_key, api_secret, paper)
    
    def place_order(self, order_data: dict) -> str:
        """Place an order on Alpaca."""
        response = self.service.place_order(order_data)
        return response.id  # Alpaca order ID
    
    def place_bracket_order(self, order_data: dict, take_profit: dict, stop_loss: dict) -> List[str]:
        """Place a bracket order on Alpaca."""
        response = self.service.place_bracket_order(
            entry_order=order_data,
            take_profit_price=take_profit.get("limit_price"),
            stop_loss_price=stop_loss.get("stop_price"),
            take_profit_limit_price=take_profit.get("limit_price"),
            stop_loss_limit_price=stop_loss.get("limit_price")
        )
        return [
            response.entry_order.id,
            response.take_profit_order.id,
            response.stop_loss_order.id
        ]
    
    def place_oco_order(self, first_leg: dict, second_leg: dict) -> List[str]:
        """Place an OCO order on Alpaca."""
        response = self.service.place_oco_order(
            first_order=first_leg,
            second_order=second_leg
        )
        return [
            response.first_order.id,
            response.second_order.id
        ]
    
    def cancel_order(self, order_id: str) -> None:
        """Cancel an order on Alpaca."""
        self.service.cancel_order(order_id)
    
    def get_order_status(self, order_id: str) -> dict:
        """Get order status from Alpaca."""
        order = self.service.get_order(order_id)
        return {
            "status": order.status,
            "filled_quantity": order.filled_qty,
            "filled_price": order.filled_avg_price
        }
