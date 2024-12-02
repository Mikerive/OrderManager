"""
Core models module. Import specific models from their respective modules:
from core.user.models import User
from core.orders.models import Order
"""

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
