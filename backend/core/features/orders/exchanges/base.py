from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ExchangeProvider(ABC):
    """Base class for exchange providers."""

    @abstractmethod
    def place_order(self, order_data: dict) -> str:
        """Place an order on the exchange.
        Returns the exchange-specific order ID."""
        pass

    @abstractmethod
    def place_bracket_order(self, order_data: dict, take_profit: dict, stop_loss: dict) -> List[str]:
        """Place a bracket order on the exchange.
        Returns a list of order IDs: [entry_order_id, take_profit_id, stop_loss_id]."""
        pass

    @abstractmethod
    def place_oco_order(self, first_leg: dict, second_leg: dict) -> List[str]:
        """Place an OCO (One-Cancels-Other) order on the exchange.
        Returns a list of order IDs: [first_leg_id, second_leg_id]."""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> None:
        """Cancel an order on the exchange."""
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> dict:
        """Get order status from the exchange."""
        pass
