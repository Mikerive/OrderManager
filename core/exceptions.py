from fastapi import HTTPException, status

class OrderChainerException(HTTPException):
    """Base exception for OrderChainer application."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class NotFoundException(OrderChainerException):
    """Resource not found exception."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class UnauthorizedException(OrderChainerException):
    """Unauthorized access exception."""
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class ForbiddenException(OrderChainerException):
    """Forbidden access exception."""
    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class BadRequestException(OrderChainerException):
    """Bad request exception."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class ConflictException(OrderChainerException):
    """Resource conflict exception."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

class UserNotFoundError(NotFoundException):
    """User not found exception."""
    def __init__(self, user_id: int = None, email: str = None):
        detail = "User not found"
        if user_id:
            detail = f"User with ID {user_id} not found"
        elif email:
            detail = f"User with email {email} not found"
        super().__init__(detail=detail)

class DuplicateUserError(ConflictException):
    """Duplicate user exception."""
    def __init__(self, email: str = None, username: str = None):
        detail = "User already exists"
        if email:
            detail = f"User with email {email} already exists"
        elif username:
            detail = f"User with username {username} already exists"
        super().__init__(detail=detail)

class OrderNotFoundError(NotFoundException):
    """Order not found exception."""
    def __init__(self, order_id: int):
        super().__init__(detail=f"Order with ID {order_id} not found")

class UnauthorizedError(UnauthorizedException):
    """Unauthorized access to order exception."""
    def __init__(self, user_id: int = None):
        detail = "Not authorized to access this order"
        if user_id:
            detail = f"User {user_id} is not authorized to access this order"
        super().__init__(detail=detail)
