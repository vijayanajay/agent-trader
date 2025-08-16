import pandas as pd
import pytest
import numpy as np
from pathlib import Path
from src.data_preprocessor import preprocess_data, _calculate_atr

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Creates a sample OHLCV DataFrame for testing."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=250))
    data = {
        "Open": np.linspace(100, 150, 250),
        "High": np.linspace(102, 152, 250),
        "Low": np.linspace(98, 148, 250),
        "Close": np.linspace(101, 151, 250),
        "Volume": np.linspace(1000, 2000, 250),
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"
    return df

def test_preprocess_happy_path(sample_df: pd.DataFrame) -> None:
    """Tests a successful run of the preprocess_data function."""
    result = preprocess_data(sample_df, "2023-08-18", window=40)

    assert result is not None
    assert isinstance(result, tuple)
    assert len(result) == 3

    df, current_price, current_atr = result

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 40
    assert df.index[-1] == pd.to_datetime("2023-08-18")

    assert "close_normalized" in df.columns
    assert "volume_normalized" in df.columns
    assert df["close_normalized"].min() >= 0.0
    assert df["close_normalized"].max() <= 1.0
    assert df["volume_normalized"].min() >= 0.0
    assert df["volume_normalized"].max() <= 1.0
    assert df["close_normalized"].iloc[-1] == 1.0

    assert current_price > 0
    assert current_atr > 0

def test_preprocess_insufficient_data(sample_df: pd.DataFrame) -> None:
    """Tests that None is returned if the lookback window is too large."""
    result = preprocess_data(sample_df, "2023-02-01", window=40)
    assert result is None

def test_preprocess_date_not_found(sample_df: pd.DataFrame) -> None:
    """Tests that None is returned if the date is not in the data."""
    result = preprocess_data(sample_df, "2025-01-01")
    assert result is None

def test_preprocess_current_date_has_nan(sample_df: pd.DataFrame) -> None:
    """Tests that None is returned if the target date has a NaN value."""
    sample_df.loc["2023-08-18", "Close"] = np.nan
    result = preprocess_data(sample_df, "2023-08-18")
    assert result is None

def test_calculate_atr_helper():
    """Tests the _calculate_atr helper function directly for correctness."""
    data = {
        "High": [10, 12, 11],
        "Low": [8, 9, 9],
        "Close": [9, 11, 10],
        "Volume": [100, 100, 100],
    }
    df = pd.DataFrame(
        data, index=pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"])
    )

    # Manual TR calculation:
    # TR1 = H-L = 10-8 = 2
    # TR2 = max(H-L, abs(H-prev_C), abs(L-prev_C)) = max(3, abs(12-9), abs(9-9)) = 3
    # TR3 = max(H-L, abs(H-prev_C), abs(L-prev_C)) = max(2, abs(11-11), abs(9-11)) = 2
    # TRs = [2, 3, 2]

    # SMA(TR, period=2)
    # ATR1 = NaN
    # ATR2 = (TR1+TR2)/2 = (2+3)/2 = 2.5
    # ATR3 = (TR2+TR3)/2 = (3+2)/2 = 2.5
    atr = _calculate_atr(df, period=2)

    assert pd.isna(atr.iloc[0]) # First ATR is NaN because of shift() for prev_close
    assert atr.iloc[1] == pytest.approx(2.5)
    assert atr.iloc[2] == pytest.approx(2.5)

def test_preprocess_flat_data_normalization(sample_df: pd.DataFrame) -> None:
    """Tests that normalization handles flat data without errors."""
    # Test flat close price
    flat_close_df = sample_df.copy()
    flat_close_df["Close"] = 100
    result = preprocess_data(flat_close_df, "2023-08-18")
    assert result is not None
    window_df = result[0]
    assert "close_normalized" in window_df.columns
    assert (window_df["close_normalized"] == 0.5).all()

    # Test flat volume
    flat_volume_df = sample_df.copy()
    flat_volume_df["Volume"] = 1000
    result = preprocess_data(flat_volume_df, "2023-08-18")
    assert result is not None
    window_df = result[0]
    assert "volume_normalized" in window_df.columns
    assert (window_df["volume_normalized"] == 0.0).all()
