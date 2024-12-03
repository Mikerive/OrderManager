from typing import Optional, Dict, Any
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import LogEntry
from features.logging.models import LogLevel

class LoggingService:
    _instance = None
    logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggingService, cls).__new__(cls)
            cls._instance.logger = None
        return cls._instance

    @classmethod
    def setup_logging(cls, log_level: LogLevel, log_file: str) -> None:
        """Set up logging configuration."""
        if cls._instance is None:
            cls._instance = cls()

        # Create logger
        logger = logging.getLogger("orderchainer")
        logger.setLevel(log_level.value)

        # Create formatters and add it to handlers
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format)

        # Create file handler
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(log_level.value)
        file_handler.setFormatter(formatter)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level.value)
        console_handler.setFormatter(formatter)

        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        cls._instance.logger = logger

    def log_message(self, level: LogLevel, message: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a message and store it in the database."""
        if self.logger is None:
            raise RuntimeError("Logger not initialized. Call setup_logging first.")

        # Format the message with source
        formatted_message = f"{source}: {message}"

        # Log to file/console
        self.logger.log(level.value, formatted_message)

        # Store in database
        db: Session = next(get_db())
        try:
            log_entry = LogEntry(
                level=level.value,
                message=message,
                source=source,
                log_metadata=metadata
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to store log entry in database: {str(e)}")
        finally:
            db.close()

    def get_logs(self, limit: int = 100, level: Optional[LogLevel] = None) -> list[LogEntry]:
        """Retrieve logs from the database."""
        db: Session = next(get_db())
        try:
            query = db.query(LogEntry)
            if level:
                query = query.filter(LogEntry.level == level.value)
            return query.order_by(LogEntry.created_at.desc()).limit(limit).all()
        finally:
            db.close()

    def clear_logs(self) -> None:
        """Clear all logs from the database."""
        db: Session = next(get_db())
        try:
            db.query(LogEntry).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to clear logs: {str(e)}")
        finally:
            db.close()

# Create a singleton instance
logging_service = LoggingService()
