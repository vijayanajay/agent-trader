import pandas as pd
import pytest
import numpy as np

from src.data_preprocessor import normalize_window


@pytest.fixture
def sample_window_df() -> pd.DataFrame:
    """Creates a sample DataFrame representing a window of data."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=40))
    data = {
        "Open": np.linspace(100, 150, 40),
        "High": np.linspace(102, 152, 40),
        "Low": np.linspace(98, 148, 40),
        "Close": np.linspace(101, 151, 40),
        "Volume": np.linspace(1000, 2000, 40),
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"
    return df


def test_normalize_window_happy_path(sample_window_df: pd.DataFrame):
    """Tests that normalization works correctly on a typical window."""
    normalized_df = normalize_window(sample_window_df)

    assert "close_normalized" in normalized_df.columns
    assert "volume_normalized" in normalized_df.columns

    # Check that min is 0 and max is 1
    assert normalized_df["close_normalized"].min() == pytest.approx(0.0)
    assert normalized_df["close_normalized"].max() == pytest.approx(1.0)
    assert normalized_df["volume_normalized"].min() == pytest.approx(0.0)
    assert normalized_df["volume_normalized"].max() == pytest.approx(1.0)

    # Check that the last value is the max (since the data is a linspace)
    assert normalized_df["close_normalized"].iloc[-1] == pytest.approx(1.0)


def test_normalize_window_flat_data(sample_window_df: pd.DataFrame):
    """Tests that normalization handles flat data without division-by-zero errors."""
    # Test flat close price
    flat_close_df = sample_window_df.copy()
    flat_close_df["Close"] = 100
    normalized_df = normalize_window(flat_close_df)
    assert "close_normalized" in normalized_df.columns
    assert (normalized_df["close_normalized"] == 0.5).all()

    # Test flat volume
    flat_volume_df = sample_window_df.copy()
    flat_volume_df["Volume"] = 1000
    normalized_df = normalize_window(flat_volume_df)
    assert "volume_normalized" in normalized_df.columns
    assert (normalized_df["volume_normalized"] == 0.0).all()

def test_normalize_window_is_pure(sample_window_df: pd.DataFrame):
    """Tests that the function does not modify the original DataFrame."""
    original_df = sample_window_df.copy()
    normalize_window(original_df)
    assert "close_normalized" not in original_df.columns, "Function should not mutate the original DataFrame"
