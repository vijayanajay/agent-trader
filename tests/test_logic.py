import pandas as pd
import pytest
from src.risk_manager import calculate_risk_parameters
from src.data_preprocessor import preprocess_data


# --- Tests for Risk Manager ---

def test_calculate_risk_parameters_happy_path():
    """Tests standard risk calculation."""
    params = calculate_risk_parameters(current_price=100.0, current_atr=5.0)
    assert params["stop_loss"] == 90.0
    assert params["take_profit"] == 120.0

def test_calculate_risk_parameters_zero_atr():
    """Tests edge case where ATR is zero."""
    params = calculate_risk_parameters(current_price=100.0, current_atr=0.0)
    assert params["stop_loss"] == 100.0
    assert params["take_profit"] == 100.0


# --- Tests for Data Preprocessor ---

@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Creates a sample DataFrame for testing the preprocessor."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=100))
    data = {
        "Open": [100 + i for i in range(100)],
        "High": [102 + i for i in range(100)],
        "Low": [98 + i for i in range(100)],
        "Close": [101 + i for i in range(100)],
        "Volume": [1000 + i * 10 for i in range(100)],
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"
    return df

def test_preprocess_data_happy_path(sample_ohlcv_data):
    """Tests a successful run of the preprocessor."""
    # Date is a string, as it comes from the backtester loop
    result = preprocess_data(sample_ohlcv_data, "2023-03-11", window_size=40)
    assert result is not None
    window, price, atr = result

    assert isinstance(window, pd.DataFrame)
    assert len(window) == 40
    assert window.index[-1] == pd.to_datetime("2023-03-11")
    # 2023-03-11 is the 70th day (index 69)
    assert price == pytest.approx(101 + 69)
    assert atr > 0

def test_preprocess_data_date_not_found(sample_ohlcv_data):
    """Tests when the analysis date does not exist."""
    result = preprocess_data(sample_ohlcv_data, "2024-01-01")
    assert result is None

def test_preprocess_data_insufficient_lookback(sample_ohlcv_data):
    """Tests when there's not enough data before the analysis date."""
    # The 20th day (index 19) doesn't have a 40-day lookback window.
    result = preprocess_data(sample_ohlcv_data, "2023-01-20", window_size=40)
    assert result is None
