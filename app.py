from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from core.database import init_db, Base, engine
from core.config import settings
from core.routes import router as auth_router
from features.logging.service import logging_service
from features.orders.routes import router as orders_router
from features.discord_integration.routes import router as discord_router
from features.logging.models import LogLevel

# Configure logging
logger = logging.getLogger(__name__)

# Initialize logging
logging_service.setup_logging(
    log_level=LogLevel[settings.LOG_LEVEL],
    log_file=settings.LOG_FILE
)
logger = logging_service.logger

# Create FastAPI application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Initializing application...")
    init_db()
    
    # Log registered routers
    logger.info("Registered Routers:")
    for route in app.routes:
        logger.info(f"  {route.path} - {route.methods}")
    
    yield
    # Shutdown
    # Add any cleanup code here if needed
    logger.info("Application shutting down...")

app = FastAPI(
    title="OrderChainer",
    description="A service for managing and chaining orders with dependencies",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
logger.info("Including routers...")
app.include_router(auth_router)  # Include auth router first
logger.info("  Included auth router")
app.include_router(orders_router)
logger.info("  Included orders router")
app.include_router(discord_router)
logger.info("  Included discord router")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to OrderChainer API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
