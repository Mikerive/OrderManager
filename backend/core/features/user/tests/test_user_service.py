import pytest
from sqlalchemy.orm import Session
from core.testing import test_db, auth_headers
from core.user.models import User
from core.user.service import UserService
from core.exceptions import UserNotFoundError, DuplicateUserError
from core.auth import get_password_hash, verify_password

@pytest.fixture
def user_service(test_db: Session):
    return UserService(test_db)

@pytest.fixture
def test_user_data():
    return {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test_password"
    }

@pytest.fixture
def test_user(user_service: UserService, test_user_data):
    return user_service.create_user(**test_user_data)

def test_create_user(user_service: UserService, test_user_data):
    user = user_service.create_user(**test_user_data)
    assert user.username == test_user_data["username"]
    assert user.email == test_user_data["email"]
    
    # Get the user from the database to verify password
    db_user = user_service.get_user_by_email(test_user_data["email"])
    assert verify_password(test_user_data["password"], db_user.hashed_password)

def test_create_duplicate_user(user_service: UserService, test_user, test_user_data):
    with pytest.raises(DuplicateUserError):
        user_service.create_user(**test_user_data)

def test_get_user(user_service: UserService, test_user):
    user = user_service.get_user(test_user.id)
    assert user.id == test_user.id
    assert user.username == test_user.username
    assert user.email == test_user.email

def test_get_user_by_username(user_service: UserService, test_user):
    user = user_service.get_user_by_username(test_user.username)
    assert user.id == test_user.id
    assert user.username == test_user.username

def test_get_user_by_email(user_service: UserService, test_user):
    user = user_service.get_user_by_email(test_user.email)
    assert user.id == test_user.id
    assert user.email == test_user.email

def test_get_nonexistent_user(user_service: UserService):
    with pytest.raises(UserNotFoundError):
        user_service.get_user(999)  # Non-existent user ID

def test_update_user(user_service: UserService, test_user):
    updated_data = {
        "email": "updated@example.com",
        "password": "new_password"
    }
    updated_user = user_service.update_user(test_user.id, **updated_data)
    assert updated_user.email == updated_data["email"]
    assert verify_password(updated_data["password"], updated_user.hashed_password)

def test_update_user_nonexistent(user_service: UserService):
    """Test updating a non-existent user raises UserNotFoundError."""
    with pytest.raises(UserNotFoundError):
        user_service.update_user(999, email="new@example.com")

def test_create_user_with_invalid_email(user_service: UserService, test_user_data):
    """Test creating a user with an invalid email format."""
    test_user_data["email"] = "invalid_email"
    with pytest.raises(ValueError):
        user_service.create_user(**test_user_data)

def test_create_user_with_empty_username(user_service: UserService, test_user_data):
    """Test creating a user with an empty username."""
    test_user_data["username"] = ""
    with pytest.raises(ValueError):
        user_service.create_user(**test_user_data)

def test_update_user_duplicate_email(user_service: UserService, test_user):
    """Test updating a user with an email that already exists."""
    # Create another user first
    other_user = user_service.create_user(
        email="other@example.com",
        username="other_user",
        password="password123"
    )
    
    # Try to update the other user with the test user's email
    with pytest.raises(DuplicateUserError):
        user_service.update_user(other_user.id, email=test_user.email)

def test_delete_user(user_service: UserService, test_user):
    user_service.delete_user(test_user.id)
    with pytest.raises(UserNotFoundError):
        user_service.get_user(test_user.id)

def test_delete_user_nonexistent(user_service: UserService):
    """Test deleting a non-existent user raises UserNotFoundError."""
    with pytest.raises(UserNotFoundError):
        user_service.delete_user(999)

def test_authenticate_user(user_service: UserService, test_user_data, test_user):
    authenticated_user = user_service.authenticate_user(
        test_user_data["email"],  # Changed from username to email
        test_user_data["password"]
    )
    assert authenticated_user is not None
    assert authenticated_user.id == test_user.id
    assert authenticated_user.email == test_user.email

def test_authenticate_user_invalid_password(user_service: UserService, test_user_data, test_user):
    authenticated_user = user_service.authenticate_user(
        test_user_data["email"],
        "wrong_password"
    )
    assert authenticated_user is None

def test_authenticate_user_invalid_username(user_service: UserService):
    authenticated_user = user_service.authenticate_user(
        "nonexistent_user@example.com",
        "any_password"
    )
    assert authenticated_user is None
