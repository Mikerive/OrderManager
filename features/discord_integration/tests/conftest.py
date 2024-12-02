import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from core.database import SessionLocal, engine
from core.models import Base, User
from main import app
from core.security import create_access_token
import bcrypt

@pytest.fixture
def test_db():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)

@pytest.fixture
def auth_headers(test_db: Session):
    """Create authentication headers with a test user."""
    # Delete existing test user if exists
    existing_user = test_db.query(User).filter_by(id=1).first()
    if existing_user:
        test_db.delete(existing_user)
        test_db.commit()

    # Create a test user with ID 1
    hashed_password = bcrypt.hashpw("testpassword".encode('utf-8'), bcrypt.gensalt())
    test_user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password=hashed_password.decode('utf-8')
    )
    test_db.add(test_user)
    test_db.commit()
    test_db.refresh(test_user)

    # Generate access token
    access_token = create_access_token(data={"sub": str(test_user.id)})
    
    return {"Authorization": f"Bearer {access_token}"}
