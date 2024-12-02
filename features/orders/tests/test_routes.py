import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.models import User, Order
from core.testing import client, test_db, auth_headers

def test_create_order(client: TestClient, auth_headers: dict):
    """Test creating a new order."""
    response = client.post(
        "/api/orders/",
        headers=auth_headers,
        json={
            "title": "Test Order",
            "description": "Test Description",
            "status": "pending",
            "dependencies": []
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Order"
    assert data["description"] == "Test Description"
    assert data["status"] == "pending"

def test_get_orders(
    client: TestClient,
    test_db: Session,
    auth_headers: dict
):
    """Test getting all orders."""
    # Create test orders
    orders = [
        Order(
            title=f"Order {i}",
            description=f"Description {i}",
            status="pending",
            owner_id=1
        )
        for i in range(3)
    ]
    for order in orders:
        test_db.add(order)
    test_db.commit()

    response = client.get("/api/orders/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(order["owner_id"] == 1 for order in data)

def test_get_order(
    client: TestClient,
    test_db: Session,
    auth_headers: dict
):
    """Test getting a specific order."""
    order = Order(
        title="Test Order",
        description="Test Description",
        status="pending",
        owner_id=1
    )
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)

    response = client.get(f"/api/orders/{order.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Order"
    assert data["owner_id"] == 1

def test_update_order(
    client: TestClient,
    test_db: Session,
    auth_headers: dict
):
    """Test updating an order."""
    order = Order(
        title="Original Title",
        description="Original Description",
        status="pending",
        owner_id=1
    )
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)

    response = client.put(
        f"/api/orders/{order.id}",
        headers=auth_headers,
        json={
            "title": "Updated Title",
            "description": "Updated Description",
            "status": "active",
            "dependencies": []
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated Description"
    assert data["status"] == "active"

def test_delete_order(
    client: TestClient,
    test_db: Session,
    auth_headers: dict
):
    """Test deleting an order."""
    order = Order(
        title="Test Order",
        description="Test Description",
        status="pending",
        owner_id=1
    )
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)

    response = client.delete(f"/api/orders/{order.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Order deleted successfully"

    # Verify order is deleted
    assert test_db.query(Order).filter(Order.id == order.id).first() is None
