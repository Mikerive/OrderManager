import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from typing import Generator, Any
import pytest
import logging
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi import Depends

from core.database.database import Base
from core.auth import get_password_hash, create_access_token, get_current_user
from core.user.models import User
from core.orders.models import Order
from features.discord_integration.models import DiscordIntegration

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create test database engine with an in-memory database
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    """Create test database tables and cleanup after test."""
    # Drop all tables first to ensure a clean state
    Base.metadata.drop_all(bind=engine)

    # Create all tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Drop tables after the test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator:
    """Create test client with test database."""
    from app import app
    
    # Override the get_db dependency to use the test database
    def get_test_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    # Ensure a test user is created
    existing_user = test_db.query(User).filter(User.email == "test@example.com").first()
    if not existing_user:
        test_user = User(
            id=1,  # Explicitly set the ID to 1
            email="test@example.com", 
            hashed_password=get_password_hash("testpassword"),
            is_active=True
        )
        test_db.add(test_user)
        test_db.commit()
        test_db.refresh(test_user)
    
    # Override authentication dependency
    def get_test_current_user():
        return test_db.query(User).filter(User.email == "test@example.com").first()
    
    # Override dependencies
    app.dependency_overrides[app.dependency_overrides.get('get_db', lambda: None)] = get_test_db
    app.dependency_overrides[get_current_user] = get_test_current_user
    
    client = TestClient(app)
    
    yield client
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def auth_headers(test_db: Session):
    """Create authentication headers for test user."""
    # Ensure test user exists
    user = test_db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(
            id=1,  # Explicitly set the ID to 1
            email="test@example.com", 
            hashed_password=get_password_hash("testpassword"),
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
    
    # Generate access token
    access_token = create_access_token(data={"sub": user.email})
    
    return {"Authorization": f"Bearer {access_token}"}
