from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .database import get_db_context, init_db as create_tables
from .models import User, Order, DiscordIntegration

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    """Initialize database with sample data."""
    # Create tables
    create_tables()
    
    with get_db_context() as db:
        # Skip if users already exist
        if db.query(User).first():
            return
        
        # Create sample users
        users = [
            {
                "email": "john@example.com",
                "password": "password123"
            },
            {
                "email": "jane@example.com",
                "password": "password456"
            }
        ]
        
        db_users = {}
        for user_data in users:
            hashed_password = pwd_context.hash(user_data["password"])
            db_user = User(email=user_data["email"], hashed_password=hashed_password)
            db.add(db_user)
            db.flush()
            db_users[user_data["email"]] = db_user
        
        # Create sample orders for John
        john = db_users["john@example.com"]
        orders = [
            {
                "title": "Initial Order",
                "description": "First order in the chain",
                "status": "completed",
                "owner_id": john.id
            },
            {
                "title": "Secondary Order",
                "description": "Depends on the initial order",
                "status": "pending",
                "owner_id": john.id
            },
            {
                "title": "Final Order",
                "description": "Depends on the secondary order",
                "status": "pending",
                "owner_id": john.id
            }
        ]
        
        # Add orders
        db_orders = []
        for order_data in orders:
            db_order = Order(**order_data)
            db.add(db_order)
            db.flush()
            db_orders.append(db_order)
        
        # Set up dependencies
        db_orders[1].dependencies.append(db_orders[0])  # Secondary depends on Initial
        db_orders[2].dependencies.append(db_orders[1])  # Final depends on Secondary
        
        # Create Discord integration for John
        discord_integration = DiscordIntegration(
            user_id=john.id,
            webhook_url="https://discord.com/api/webhooks/example",
            webhook_username="OrderChainer Bot",
            notify_order_created=True,
            notify_order_updated=True,
            notify_order_completed=True,
            notify_order_failed=True
        )
        db.add(discord_integration)
        
        # Commit all changes
        db.commit()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("\nDatabase initialized successfully!")
    print("\nSample Accounts:")
    print("Email: john@example.com")
    print("Password: password123")
    print("\nEmail: jane@example.com")
    print("Password: password456")
