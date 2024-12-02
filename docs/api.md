# OrderChainer API Documentation

## Authentication

### Register New User
```http
POST /api/auth/register
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response**:
```json
{
  "email": "user@example.com",
  "id": 1,
  "is_active": true
}
```

### Login (Get Access Token)
```http
POST /api/auth/token
```

**Request Body**:
```json
{
  "username": "user@example.com",
  "password": "securepassword"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

## Orders

### Create Order
```http
POST /api/orders/
Authorization: Bearer {token}
```

**Request Body**:
```json
{
  "title": "New Order",
  "description": "Order description",
  "status": "pending",
  "dependencies": [1, 2]
}
```

**Response**:
```json
{
  "id": 3,
  "title": "New Order",
  "description": "Order description",
  "status": "pending",
  "created_at": "2024-02-14T12:00:00",
  "updated_at": "2024-02-14T12:00:00",
  "owner_id": 1
}
```

### List Orders
```http
GET /api/orders/
Authorization: Bearer {token}
```

**Query Parameters**:
- `skip` (optional): Number of records to skip
- `limit` (optional): Maximum number of records to return

**Response**:
```json
[
  {
    "id": 1,
    "title": "First Order",
    "description": "First order description",
    "status": "completed",
    "created_at": "2024-02-14T10:00:00",
    "updated_at": "2024-02-14T11:00:00",
    "owner_id": 1
  }
]
```

### Get Order
```http
GET /api/orders/{order_id}
Authorization: Bearer {token}
```

**Response**:
```json
{
  "id": 1,
  "title": "First Order",
  "description": "First order description",
  "status": "completed",
  "created_at": "2024-02-14T10:00:00",
  "updated_at": "2024-02-14T11:00:00",
  "owner_id": 1
}
```

### Update Order
```http
PUT /api/orders/{order_id}
Authorization: Bearer {token}
```

**Request Body**:
```json
{
  "title": "Updated Order",
  "description": "Updated description",
  "status": "active",
  "dependencies": [1]
}
```

**Response**:
```json
{
  "id": 2,
  "title": "Updated Order",
  "description": "Updated description",
  "status": "active",
  "created_at": "2024-02-14T10:00:00",
  "updated_at": "2024-02-14T12:00:00",
  "owner_id": 1
}
```

### Delete Order
```http
DELETE /api/orders/{order_id}
Authorization: Bearer {token}
```

**Response**:
```json
{
  "message": "Order deleted successfully"
}
```

## Discord Integration

### Create Integration
```http
POST /api/discord/
Authorization: Bearer {token}
```

**Request Body**:
```json
{
  "webhook": {
    "url": "https://discord.com/api/webhooks/...",
    "username": "OrderChainer Bot",
    "avatar_url": "https://example.com/avatar.png"
  },
  "notifications": {
    "order_created": true,
    "order_updated": true,
    "order_completed": true,
    "order_failed": true
  }
}
```

**Response**:
```json
{
  "id": 1,
  "user_id": 1,
  "webhook": {
    "url": "https://discord.com/api/webhooks/...",
    "username": "OrderChainer Bot",
    "avatar_url": "https://example.com/avatar.png"
  },
  "notifications": {
    "order_created": true,
    "order_updated": true,
    "order_completed": true,
    "order_failed": true
  },
  "is_active": true
}
```

### Get Integration
```http
GET /api/discord/
Authorization: Bearer {token}
```

**Response**: Same as Create Integration response

### Update Integration
```http
PUT /api/discord/
Authorization: Bearer {token}
```

**Request Body**:
```json
{
  "webhook": {
    "url": "https://discord.com/api/webhooks/...",
    "username": "Updated Bot Name"
  },
  "notifications": {
    "order_completed": false
  }
}
```

**Response**: Same as Create Integration response with updated fields

### Delete Integration
```http
DELETE /api/discord/
Authorization: Bearer {token}
```

**Response**:
```json
{
  "message": "Discord integration deleted successfully"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized to perform this action"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 409 Conflict
```json
{
  "detail": "Resource already exists"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```
