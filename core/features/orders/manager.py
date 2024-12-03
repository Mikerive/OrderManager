from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from .models import Order, OrderStatus
from ..features import FeatureRegistry
from core.exceptions import OrderNotFoundError, UnauthorizedError
from core.user.models import User

class OrderManager:
    """Core order management functionality."""
    
    @staticmethod
    async def create_order(db: Session, user_id: int, order_data: dict) -> Order:
        """Create a new order and place it on the specified exchange."""
        # Validate user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError()
            
        # Get exchange provider
        exchange_type = order_data.get("exchange_type")
        if not exchange_type:
            raise ValueError("Exchange type must be specified")
            
        exchange = FeatureRegistry.get_exchange(exchange_type)
        if not exchange:
            raise ValueError(f"Exchange provider not found: {exchange_type}")
        
        # Create order in database
        order = Order(
            owner_id=user.id,
            title=order_data["title"],
            description=order_data.get("description"),
            status=OrderStatus.PENDING,
            symbol=order_data["symbol"],
            quantity=order_data["quantity"],
            order_type=order_data["order_type"],
            side=order_data["side"],
            price=order_data.get("price"),
            stop_price=order_data.get("stop_price"),
            limit_price=order_data.get("limit_price"),
            provider=exchange_type,
            chain_id=order_data.get("chain_id"),
            chain_type=order_data.get("chain_type"),
            chain_sequence=order_data.get("chain_sequence"),
            parent_order_id=order_data.get("parent_order_id")
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        try:
            # Place order on exchange
            provider_order_id = exchange.place_order({
                "symbol": order.symbol,
                "quantity": order.quantity,
                "order_type": order.order_type,
                "side": order.side,
                "limit_price": order.limit_price,
                "stop_price": order.stop_price,
                "time_in_force": order_data.get("time_in_force", "day"),
                "extended_hours": order_data.get("extended_hours", False)
            })
            
            # Update order with provider ID
            order.provider_order_id = provider_order_id
            order.status = OrderStatus.ACTIVE
            db.commit()
            
        except Exception as e:
            order.status = OrderStatus.FAILED
            order.additional_data = {"error": str(e)}
            db.commit()
            raise
        
        return order
    
    @staticmethod
    async def create_bracket_order(
        db: Session,
        user_id: int,
        entry_order: dict,
        take_profit: dict,
        stop_loss: dict,
        exchange_type: str
    ) -> List[Order]:
        """Create a bracket order (entry + take profit + stop loss)."""
        exchange = FeatureRegistry.get_exchange(exchange_type)
        if not exchange:
            raise ValueError(f"Exchange provider not found: {exchange_type}")
            
        # Generate chain ID
        import uuid
        chain_id = str(uuid.uuid4())
        
        try:
            # Place bracket order on exchange
            [entry_id, tp_id, sl_id] = exchange.place_bracket_order(
                entry_order,
                take_profit,
                stop_loss
            )
            
            # Create orders in database
            orders = []
            
            # Entry order
            entry = await OrderManager.create_order(db, user_id, {
                **entry_order,
                "chain_id": chain_id,
                "chain_type": "bracket",
                "chain_sequence": 0,
                "exchange_type": exchange_type,
                "provider_order_id": entry_id
            })
            orders.append(entry)
            
            # Take profit order
            tp = await OrderManager.create_order(db, user_id, {
                **take_profit,
                "chain_id": chain_id,
                "chain_type": "bracket",
                "chain_sequence": 1,
                "parent_order_id": entry.id,
                "exchange_type": exchange_type,
                "provider_order_id": tp_id
            })
            orders.append(tp)
            
            # Stop loss order
            sl = await OrderManager.create_order(db, user_id, {
                **stop_loss,
                "chain_id": chain_id,
                "chain_type": "bracket",
                "chain_sequence": 2,
                "parent_order_id": entry.id,
                "exchange_type": exchange_type,
                "provider_order_id": sl_id
            })
            orders.append(sl)
            
            return orders
            
        except Exception as e:
            # If anything fails, cancel any orders that were placed
            for order in orders:
                if order.provider_order_id:
                    try:
                        exchange.cancel_order(order.provider_order_id)
                    except:
                        pass
            raise
    
    @staticmethod
    async def cancel_order(db: Session, order_id: int, user_id: int) -> Order:
        """Cancel an order."""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise OrderNotFoundError(f"Order not found: {order_id}")
            
        if order.owner_id != user_id:
            raise UnauthorizedError()
            
        if order.provider_order_id:
            exchange = FeatureRegistry.get_exchange(order.provider)
            if exchange:
                try:
                    exchange.cancel_order(order.provider_order_id)
                    order.status = OrderStatus.CANCELLED
                    db.commit()
                except Exception as e:
                    order.additional_data = {"cancel_error": str(e)}
                    db.commit()
                    raise
        
        return order
