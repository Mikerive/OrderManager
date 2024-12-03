from typing import List, Dict, Set, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from core.orders.models import Order, OrderEdge, OrderCreate, OrderStatus
from core.database.database import get_db

class OrderGraphService:
    """Service for managing the order dependency graph."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_order_chain(self, orders: List[OrderCreate], user_id: int) -> List[Order]:
        """
        Create a chain of orders with their dependencies.
        
        Args:
            orders: List of orders to create
            user_id: ID of the user creating the orders
        
        Returns:
            List of created orders
        """
        # Create all orders first
        created_orders: List[Order] = []
        order_map: Dict[int, Order] = {}  # Map temp IDs to created orders
        
        for i, order_create in enumerate(orders):
            order = Order(
                title=order_create.title,
                description=order_create.description,
                status=OrderStatus.PENDING,
                order_type=order_create.order_type.value,
                side=order_create.side.value,
                symbol=order_create.symbol,
                quantity=order_create.quantity,
                price=order_create.price,
                stop_price=order_create.stop_price,
                limit_price=order_create.limit_price,
                trail_percent=order_create.trail_percent,
                trail_price=order_create.trail_price,
                additional_data=order_create.additional_data,
                owner_id=user_id,
                provider=order_create.provider
            )
            self.db.add(order)
            self.db.flush()  # Get the order ID
            created_orders.append(order)
            order_map[i] = order
        
        # Create dependencies
        for i, order_create in enumerate(orders):
            order = order_map[i]
            for edge in order_create.dependencies:
                dependency = order_map[edge.to_order_id]
                # Add dependency relationship with condition data
                self.db.execute(
                    order_dependencies.insert().values(
                        dependent_order_id=order.id,
                        dependency_order_id=dependency.id,
                        condition_type=edge.condition_type,
                        condition_data=edge.condition_data
                    )
                )
        
        self.db.commit()
        return created_orders
    
    def get_ready_orders(self, user_id: Optional[int] = None) -> List[Order]:
        """
        Get orders that are ready to be executed (have no pending dependencies).
        
        Args:
            user_id: Optional user ID to filter orders
        
        Returns:
            List of orders ready to be executed
        """
        query = self.db.query(Order).filter(
            Order.status == OrderStatus.PENDING,
            ~Order.id.in_(
                self.db.query(order_dependencies.c.dependent_order_id)
                .join(Order, order_dependencies.c.dependency_order_id == Order.id)
                .filter(Order.status != OrderStatus.FILLED)
                .subquery()
            )
        )
        
        if user_id is not None:
            query = query.filter(Order.owner_id == user_id)
        
        return query.all()
    
    def update_order_status(self, order_id: int, status: OrderStatus) -> Order:
        """
        Update the status of an order and process any dependent orders.
        
        Args:
            order_id: ID of the order to update
            status: New status for the order
        
        Returns:
            Updated order
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        order.status = status
        order.updated_at = datetime.utcnow()
        
        # If order is filled, check dependent orders
        if status == OrderStatus.FILLED:
            # Get all dependent orders that might be ready
            dependent_orders = (
                self.db.query(Order)
                .join(
                    order_dependencies,
                    order_dependencies.c.dependent_order_id == Order.id
                )
                .filter(
                    order_dependencies.c.dependency_order_id == order_id,
                    Order.status == OrderStatus.PENDING
                )
                .all()
            )
            
            # Check each dependent order
            for dep_order in dependent_orders:
                # Check if all dependencies are filled
                all_deps_filled = all(
                    dep.status == OrderStatus.FILLED
                    for dep in dep_order.dependencies
                )
                
                if all_deps_filled:
                    dep_order.status = OrderStatus.ACTIVE
                    dep_order.updated_at = datetime.utcnow()
        
        self.db.commit()
        return order
    
    def cancel_dependent_orders(self, order_id: int) -> List[Order]:
        """
        Cancel all orders that depend on the given order.
        
        Args:
            order_id: ID of the failed/cancelled order
        
        Returns:
            List of cancelled orders
        """
        # Get all dependent orders recursively
        def get_all_dependents(order_id: int, seen: Set[int]) -> Set[int]:
            if order_id in seen:
                return seen
            
            seen.add(order_id)
            dependents = (
                self.db.query(Order.id)
                .join(
                    order_dependencies,
                    order_dependencies.c.dependent_order_id == Order.id
                )
                .filter(order_dependencies.c.dependency_order_id == order_id)
                .all()
            )
            
            for (dep_id,) in dependents:
                get_all_dependents(dep_id, seen)
            
            return seen
        
        # Get all dependent order IDs
        dependent_ids = get_all_dependents(order_id, set()) - {order_id}
        
        # Cancel all dependent orders
        cancelled_orders = []
        for dep_id in dependent_ids:
            order = self.db.query(Order).filter(Order.id == dep_id).first()
            if order and order.status not in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.utcnow()
                cancelled_orders.append(order)
        
        self.db.commit()
        return cancelled_orders
    
    def get_order_chain(self, root_order_id: int) -> Dict[int, List[OrderEdge]]:
        """
        Get the entire chain of orders starting from the given root order.
        
        Args:
            root_order_id: ID of the root order
        
        Returns:
            Dictionary mapping order IDs to their outgoing edges
        """
        chain: Dict[int, List[OrderEdge]] = {}
        
        def build_chain(order_id: int, seen: Set[int]):
            if order_id in seen:
                return
            
            seen.add(order_id)
            edges = (
                self.db.query(
                    order_dependencies.c.dependent_order_id,
                    order_dependencies.c.dependency_order_id,
                    order_dependencies.c.condition_type,
                    order_dependencies.c.condition_data
                )
                .filter(order_dependencies.c.dependent_order_id == order_id)
                .all()
            )
            
            chain[order_id] = [
                OrderEdge(
                    from_order_id=dep_id,
                    to_order_id=order_id,
                    condition_type=condition_type,
                    condition_data=condition_data
                )
                for dep_id, order_id, condition_type, condition_data in edges
            ]
            
            for edge in chain[order_id]:
                build_chain(edge.to_order_id, seen)
        
        build_chain(root_order_id, set())
        return chain
