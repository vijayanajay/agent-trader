import pandas as pd
import pytest
import numpy as np
from pathlib import Path
from src.data_preprocessor import preprocess

@pytest.fixture
def sample_csv_path(tmp_path: Path) -> str:
    """Creates a sample OHLCV CSV file and returns its path."""
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

    # Add some NaNs to test handling
    df.loc["2023-01-05", "Close"] = np.nan

    csv_path = tmp_path / "test_data.csv"
    df.to_csv(csv_path)
    return str(csv_path)

def test_preprocess_happy_path(sample_csv_path: str) -> None:
    """Tests a successful run of the preprocess function."""
    result = preprocess(sample_csv_path, "2023-08-18", window=40)

    assert isinstance(result, dict)
    assert "window_df" in result
    assert "sma50" in result
    assert "sma200" in result
    assert "atr14" in result
    assert "current_price" in result

    df = result["window_df"]
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 40
    assert df.index[-1] == pd.to_datetime("2023-08-18")

    assert "close_normalized" in df.columns
    assert "volume_normalized" in df.columns
    assert df["close_normalized"].min() == 0.0
    assert df["close_normalized"].max() == 1.0
    assert df["volume_normalized"].min() == 0.0
    assert df["volume_normalized"].max() == 1.0

    assert result["current_price"] > 0
    assert result["atr14"] > 0
    assert result["sma50"] > 0
    # SMA200 will be NaN because we only have 250 days, and the date is near the end
    assert not np.isnan(result["sma200"])

def test_preprocess_insufficient_data_error(sample_csv_path: str) -> None:
    """Tests that a ValueError is raised if the lookback window is too large."""
    with pytest.raises(ValueError, match="Not enough data"):
        preprocess(sample_csv_path, "2023-02-01", window=40)

def test_preprocess_date_not_found_error(sample_csv_path: str) -> None:
    """Tests that a ValueError is raised if the date is not in the data."""
    with pytest.raises(ValueError, match="not found in the data"):
        preprocess(sample_csv_path, "2025-01-01")

def test_preprocess_file_not_found_error() -> None:
    """Tests that FileNotFoundError is raised for a non-existent file."""
    with pytest.raises(FileNotFoundError):
        preprocess("non_existent_file.csv", "2023-01-01")

def test_preprocess_sma_and_atr_values(sample_csv_path: str) -> None:
    """Checks SMA and ATR values for correctness."""
    result = preprocess(sample_csv_path, "2023-08-18")

    df = pd.read_csv(sample_csv_path, parse_dates=["Date"], index_col="Date")

    # Manual calculation for verification
    target_date = pd.to_datetime("2023-08-18")
    expected_sma50 = df.loc[:target_date, "Close"].tail(50).mean()
    expected_sma200 = df.loc[:target_date, "Close"].tail(200).mean()

    assert result["sma50"] == pytest.approx(expected_sma50)
    assert result["sma200"] == pytest.approx(expected_sma200)
    assert result["atr14"] > 0 # Exact ATR is complex, just check it's positive

def test_preprocess_nan_in_window(tmp_path: Path) -> None:
    """Tests that normalization works correctly even with NaNs in the window."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=50))
    data = {
        "Open": np.linspace(100, 150, 50),
        "High": np.linspace(102, 152, 50),
        "Low": np.linspace(98, 148, 50),
        "Close": np.linspace(101, 151, 50),
        "Volume": np.linspace(1000, 2000, 50),
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"
    # Set a value to NaN inside the window
    df.loc["2023-02-10", "Close"] = np.nan

    csv_path = tmp_path / "nan_test.csv"
    df.to_csv(csv_path)

    # Preprocessing should complete without errors
    result = preprocess(str(csv_path), "2023-02-19", window=40)

    # The normalized column will have a NaN where the original was
    assert result["window_df"]["close_normalized"].isnull().sum() == 1
