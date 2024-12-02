# OrderChainer

OrderChainer is a FastAPI-based service for managing and chaining orders with dependencies. It provides a robust API for order management with Discord integration for notifications.

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Create `.env` file in the root directory:
   ```env
   DATABASE_URL=sqlite:///./orderchainer.db
   SECRET_KEY=your-secret-key-here
   LOG_LEVEL=INFO
   LOG_FILE=logs/orderchainer.log
   ```

3. **Initialize Database**
   ```bash
   python -c "from core.init_db import init_db; init_db()"
   ```

4. **Run the Application**
   ```bash
   uvicorn app:app --reload
   ```

   Access the API at:
   - API: http://127.0.0.1:8000
   - Documentation: http://127.0.0.1:8000/docs

## Documentation

Detailed documentation is available in the `docs` directory:

- [Setup Guide](docs/setup.md) - Complete installation and configuration instructions
- [Features](docs/features.md) - Detailed feature documentation
- [Technologies](docs/technologies.md) - Overview of technologies used
- [API Documentation](docs/api.md) - Complete API reference

## Key Features

- **Order Management**
  - Create and manage orders
  - Define order dependencies
  - Track order status

- **Discord Integration**
  - Webhook notifications
  - Customizable alerts
  - Status updates

- **Authentication**
  - JWT-based authentication
  - Secure password handling
  - User management

## Sample Accounts

The database comes with two sample accounts:

1. **John Doe**
   - Email: `john@example.com`
   - Password: `password123`

2. **Jane Doe**
   - Email: `jane@example.com`
   - Password: `password456`

## Project Structure

```
OrderChainer/
├── core/               # Core application components
├── features/          # Feature modules
│   ├── orders/        # Order management
│   ├── discord/       # Discord integration
│   └── logging/       # Logging utilities
├── docs/              # Documentation
├── logs/              # Application logs
├── app.py            # Main application
├── requirements.txt  # Dependencies
└── .env             # Environment variables
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
