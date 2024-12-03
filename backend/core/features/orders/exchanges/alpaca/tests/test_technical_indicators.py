import pytest
from unittest.mock import Mock, patch
import numpy as np
from datetime import datetime, timezone, timedelta
from features.alpaca.service import AlpacaService
from features.alpaca.models import (
    TechnicalIndicatorType,
    TechnicalIndicatorRequest,
    TechnicalIndicatorResult
)

@pytest.fixture
def mock_order_service():
    return Mock()

@pytest.fixture
def alpaca_service(mock_order_service):
    service = AlpacaService(order_service=mock_order_service)
    service._data_client = Mock()
    return service

def test_calculate_rsi():
    # Create sample price data
    prices = np.array([
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
        45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28
    ])
    
    gains = np.array([0.0] + [max(0, prices[i] - prices[i-1]) for i in range(1, len(prices))])
    losses = np.array([0.0] + [max(0, prices[i-1] - prices[i]) for i in range(1, len(prices))])
    
    avg_gain = np.mean(gains[1:15])  # First 14 periods
    avg_loss = np.mean(losses[1:15])
    
    expected_rsi = 100 - (100 / (1 + (avg_gain / avg_loss)))
    
    # Calculate RSI using service method
    rsi = AlpacaService.calculate_rsi(prices, period=14)
    
    assert abs(rsi - expected_rsi) < 0.01  # Allow small floating point differences

def test_calculate_macd():
    # Create sample price data
    prices = np.array([
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
        45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28,
        46.07, 45.70, 46.45, 45.78, 45.35, 44.03, 44.18, 44.22,
        44.57, 43.42, 42.66, 43.13
    ])
    
    # Calculate expected MACD values
    exp12 = prices.ewm(span=12, adjust=False).mean()
    exp26 = prices.ewm(span=26, adjust=False).mean()
    expected_macd_line = exp12 - exp26
    expected_signal_line = expected_macd_line.ewm(span=9, adjust=False).mean()
    expected_histogram = expected_macd_line - expected_signal_line
    
    # Calculate MACD using service method
    macd_line, signal_line, histogram = AlpacaService.calculate_macd(prices)
    
    # Compare last values
    assert abs(macd_line[-1] - expected_macd_line.iloc[-1]) < 0.01
    assert abs(signal_line[-1] - expected_signal_line.iloc[-1]) < 0.01
    assert abs(histogram[-1] - expected_histogram.iloc[-1]) < 0.01

@pytest.mark.asyncio
async def test_get_technical_indicators(alpaca_service):
    # Mock bars response
    mock_bars = [
        Mock(close=price) for price in [
            44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
            45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28
        ]
    ]
    alpaca_service._data_client.get_stock_bars.return_value = {"AAPL": mock_bars}
    
    # Create indicator request
    request = TechnicalIndicatorRequest(
        symbol="AAPL",
        indicators=[
            TechnicalIndicatorType.RSI,
            TechnicalIndicatorType.MACD
        ],
        period=14
    )
    
    # Get indicators
    result = await alpaca_service.get_technical_indicators(request)
    
    assert isinstance(result, TechnicalIndicatorResult)
    assert result.symbol == "AAPL"
    assert "RSI" in result.indicators
    assert "MACD" in result.indicators
    assert isinstance(result.indicators["RSI"], float)
    assert isinstance(result.indicators["MACD"], dict)
    assert all(k in result.indicators["MACD"] for k in ["macd", "signal", "histogram"])

@pytest.mark.asyncio
async def test_get_technical_indicators_insufficient_data(alpaca_service):
    # Mock bars response with insufficient data
    mock_bars = [Mock(close=44.34), Mock(close=44.09)]  # Only 2 data points
    alpaca_service._data_client.get_stock_bars.return_value = {"AAPL": mock_bars}
    
    # Create indicator request
    request = TechnicalIndicatorRequest(
        symbol="AAPL",
        indicators=[TechnicalIndicatorType.RSI],
        period=14  # Requires at least 14 data points
    )
    
    # Verify exception is raised
    with pytest.raises(ValueError, match="Insufficient data"):
        await alpaca_service.get_technical_indicators(request)

@pytest.mark.asyncio
async def test_get_technical_indicators_invalid_symbol(alpaca_service):
    # Mock bars response with no data
    alpaca_service._data_client.get_stock_bars.return_value = {}
    
    # Create indicator request with invalid symbol
    request = TechnicalIndicatorRequest(
        symbol="INVALID",
        indicators=[TechnicalIndicatorType.RSI],
        period=14
    )
    
    # Verify exception is raised
    with pytest.raises(ValueError, match="No data available"):
        await alpaca_service.get_technical_indicators(request)

def test_calculate_moving_average():
    # Create sample price data
    prices = np.array([
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
        45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28
    ])
    
    # Calculate expected SMA
    period = 5
    expected_sma = np.convolve(prices, np.ones(period)/period, mode='valid')
    
    # Calculate SMA using service method
    sma = AlpacaService.calculate_moving_average(prices, period=period)
    
    # Compare results
    assert len(sma) == len(expected_sma)
    assert all(abs(a - b) < 0.01 for a, b in zip(sma, expected_sma))

def test_calculate_bollinger_bands():
    # Create sample price data
    prices = np.array([
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
        45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28
    ])
    
    period = 5
    num_std = 2
    
    # Calculate expected values
    rolling_mean = np.convolve(prices, np.ones(period)/period, mode='valid')
    rolling_std = np.array([np.std(prices[i:i+period]) for i in range(len(prices)-period+1)])
    
    expected_upper = rolling_mean + (num_std * rolling_std)
    expected_lower = rolling_mean - (num_std * rolling_std)
    
    # Calculate Bollinger Bands using service method
    upper, middle, lower = AlpacaService.calculate_bollinger_bands(prices, period=period, num_std=num_std)
    
    # Compare results
    assert len(upper) == len(expected_upper)
    assert len(lower) == len(expected_lower)
    assert all(abs(a - b) < 0.01 for a, b in zip(upper, expected_upper))
    assert all(abs(a - b) < 0.01 for a, b in zip(lower, expected_lower))
    assert all(abs(a - b) < 0.01 for a, b in zip(middle, rolling_mean))
