# Alpaca Trading Integration

This module provides integration between our order management system and Alpaca's trading platform. It allows users to:
- Place and manage trades through Alpaca while tracking them in our order system
- View portfolio and position information
- Get real-time stock quotes
- Track order status and sync with our local database

## Features

- Full integration with our order management system
- Support for both paper and live trading
- Real-time order status synchronization
- Comprehensive error handling and validation
- Support for various order types (market, limit, stop, stop-limit)

## Environment Setup

1. Create a `.env` file in the `features/alpaca` directory by copying `.env.example`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your Alpaca API credentials in the `.env` file:
   ```env
   ALPACA_API_KEY=your_api_key_here
   ALPACA_API_SECRET=your_api_secret_here
   ALPACA_ENVIRONMENT=paper  # Use 'paper' for testing or 'live' for real trading
   ```

3. Make sure to add `.env` to your `.gitignore` to prevent committing sensitive credentials:
   ```gitignore
   # Alpaca environment variables
   features/alpaca/.env
   ```

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```python
from features.alpaca.service import AlpacaService
from features.alpaca.models import (
    AlpacaCredentials,
    AlpacaEnvironment,
    AlpacaOrderRequest,
    AlpacaOrderSide,
    AlpacaOrderType
)

# Initialize the service
service = AlpacaService(order_service)
await service.initialize(AlpacaCredentials(
    api_key="your_api_key",
    api_secret="your_api_secret",
    environment=AlpacaEnvironment.PAPER
))

# Place a market order
order = await service.place_order(
    user=current_user,
    order_request=AlpacaOrderRequest(
        symbol="AAPL",
        qty=100,
        side=AlpacaOrderSide.BUY,
        type=AlpacaOrderType.MARKET
    )
)

# Get real-time quote
quote = await service.get_stock_quote("AAPL")
print(f"Current Ask: ${quote['ask_price']:,.2f}")

# Sync order status
await service.sync_order_status(order)
```

## Integration with Order Management

The Alpaca service automatically creates and updates managed orders in our system:

1. When placing an order through Alpaca:
   - Creates a managed order with appropriate status
   - Tags it with relevant information (symbol, side, type)
   - Stores Alpaca order ID in the notes field

2. When syncing order status:
   - Fetches current status from Alpaca
   - Updates our managed order status accordingly
   - Maintains consistency between systems

## Error Handling

The service includes comprehensive error handling for:
- Authentication failures
- Invalid order parameters
- Network issues
- API rate limiting
- Order validation

## Security Notes

1. Never commit your `.env` file or expose your Alpaca credentials
2. Use environment variables for sensitive information
3. Always use paper trading for testing
4. Regularly sync and validate order statuses

## Testing

Run the test suite:
```bash
pytest features/alpaca/tests/
```

The test suite includes:
- Unit tests for all service methods
- Integration tests with mock API responses
- Error handling and edge case testing
