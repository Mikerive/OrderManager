# OrderChainer Setup Guide

This guide will walk you through setting up the OrderChainer application.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for version control)

## Installation Steps

1. **Clone or Download the Repository**
   ```bash
   git clone <repository-url>
   cd OrderChainer
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/MacOS
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Create a `.env` file in the root directory with the following content:
   ```env
   DATABASE_URL=sqlite:///./orderchainer.db
   SECRET_KEY=your-secret-key-here
   LOG_LEVEL=INFO
   LOG_FILE=logs/orderchainer.log
   ```
   
   > **Note**: In production, replace `your-secret-key-here` with a secure secret key.

5. **Initialize the Database**
   ```bash
   python -c "from core.init_db import init_db; init_db()"
   ```
   
   This will create:
   - Database tables
   - Sample user accounts
   - Example orders with dependencies

6. **Start the Application**
   ```bash
   uvicorn app:app --reload
   ```
   
   The API will be available at:
   - API: `http://127.0.0.1:8000`
   - Swagger UI: `http://127.0.0.1:8000/docs`
   - ReDoc: `http://127.0.0.1:8000/redoc`

## Sample Accounts

The database initialization creates two sample accounts:

1. **John Doe**
   - Email: `john@example.com`
   - Password: `password123`

2. **Jane Doe**
   - Email: `jane@example.com`
   - Password: `password456`

## Directory Structure

```
OrderChainer/
├── core/               # Core application components
├── features/           # Feature modules
├── logs/              # Application logs
├── docs/              # Documentation
├── app.py             # Main application entry
├── requirements.txt   # Dependencies
└── .env              # Environment variables
```

## Troubleshooting

1. **Database Issues**
   - Ensure SQLite is working correctly
   - Check database file permissions
   - Verify DATABASE_URL in .env

2. **Authentication Issues**
   - Confirm SECRET_KEY is set in .env
   - Check user credentials
   - Verify token expiration

3. **Logging Issues**
   - Ensure logs directory exists
   - Check write permissions
   - Verify LOG_FILE path in .env
