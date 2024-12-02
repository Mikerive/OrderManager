from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy.orm import Session

from features.logging.service import LoggingService, logging_service
from features.logging.models import LogLevel
from core.models import LogEntry

@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging before each test."""
    # Reset the singleton instance
    LoggingService._instance = None
    
    with patch('logging.getLogger') as mock_logger:
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        LoggingService.setup_logging(
            log_level=LogLevel.INFO,
            log_file="test.log"
        )
        
        yield mock_logger_instance

def test_setup_logging(tmp_path: Path):
    """Test logging setup configuration."""
    log_file = tmp_path / "test.log"
    
    # Reset the singleton instance
    LoggingService._instance = None
    
    with patch('logging.getLogger') as mock_logger:
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        LoggingService.setup_logging(
            log_level=LogLevel.INFO,
            log_file=str(log_file)
        )
        
        # Verify logger was configured correctly
        mock_logger.assert_called_once_with("orderchainer")
        assert mock_logger_instance.setLevel.called
        assert len(mock_logger_instance.addHandler.call_args_list) == 2  # Console and file handler

def test_singleton_instance():
    """Test that LoggingService maintains singleton instance."""
    # Reset the singleton instance
    LoggingService._instance = None
    
    # Create two instances
    service1 = LoggingService()
    service2 = LoggingService()
    
    # Verify they are the same instance
    assert service1 is service2
    assert LoggingService._instance is service1

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    mock_session = MagicMock(spec=Session)
    return mock_session

def test_log_message(setup_logging):
    """Test logging a message."""
    # Get service instance and log message
    service = LoggingService()
    with patch('core.database.get_db') as mock_get_db:
        mock_session = MagicMock()
        mock_get_db.return_value = iter([mock_session])
        
        service.log_message(
            level=LogLevel.INFO,
            message="Test message",
            source="test_service"
        )
        
        # Verify logging occurred
        setup_logging.log.assert_called_once_with(
            LogLevel.INFO.value,
            "test_service: Test message"
        )
        
        # Verify database entry was created
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

def test_get_logs(setup_logging):
    """Test retrieving logs from database."""
    service = LoggingService()
    with patch('core.database.get_db') as mock_get_db:
        mock_session = MagicMock()
        mock_get_db.return_value = iter([mock_session])
        
        # Mock query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Test get_logs
        logs = service.get_logs(limit=10, level=LogLevel.INFO)
        
        # Verify query was constructed correctly
        mock_session.query.assert_called_once_with(LogEntry)
        mock_query.order_by.assert_called_once()
        mock_query.limit.assert_called_once_with(10)
        assert logs == []

def test_clear_logs(setup_logging):
    """Test clearing logs from database."""
    service = LoggingService()
    with patch('core.database.get_db') as mock_get_db:
        mock_session = MagicMock()
        mock_get_db.return_value = iter([mock_session])
        
        # Test clear_logs
        service.clear_logs()
        
        # Verify logs were cleared
        mock_session.query.assert_called_once_with(LogEntry)
        mock_session.query.return_value.delete.assert_called_once()
        mock_session.commit.assert_called_once()
