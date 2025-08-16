import pandas as pd
import pytest
import numpy as np

from src.data_preprocessor import preprocess_data


@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    """Creates a sample OHLCV DataFrame with enough data for indicators."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=100))
    data = {
        "Open": np.linspace(100, 200, 100),
        "High": np.linspace(102, 202, 100),
        "Low": np.linspace(98, 198, 100),
        "Close": np.linspace(101, 201, 100),
        "Volume": np.linspace(1000, 2000, 100),
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"
    return df


def test_preprocess_data_adds_columns(sample_ohlcv_df: pd.DataFrame):
    """Tests that preprocess_data adds the expected sma50 and atr14 columns."""
    processed_df = preprocess_data(sample_ohlcv_df, sma_period=50, atr_period=14)

    assert "sma50" in processed_df.columns
    assert "atr14" in processed_df.columns


def test_preprocess_data_removes_nans(sample_ohlcv_df: pd.DataFrame):
    """Tests that no NaN values exist in the processed DataFrame."""
    processed_df = preprocess_data(sample_ohlcv_df, sma_period=50, atr_period=14)

    assert not processed_df.isnull().values.any()
    # The first 49 rows of the original df should be dropped due to SMA(50) calculation.
    assert len(processed_df) == len(sample_ohlcv_df) - 49


def test_preprocess_data_is_pure(sample_ohlcv_df: pd.DataFrame):
    """Tests that the function does not modify the original DataFrame."""
    original_df_copy = sample_ohlcv_df.copy()
    preprocess_data(sample_ohlcv_df, sma_period=50, atr_period=14)

    assert "sma50" not in sample_ohlcv_df.columns, "Function should not mutate the original DataFrame"
    assert "atr14" not in sample_ohlcv_df.columns, "Function should not mutate the original DataFrame"
    pd.testing.assert_frame_equal(original_df_copy, sample_ohlcv_df)


def test_preprocess_data_calculation(sample_ohlcv_df: pd.DataFrame):
    """Performs a sanity check on the first calculated SMA value."""
    processed_df = preprocess_data(sample_ohlcv_df, sma_period=50, atr_period=14)

    # The first row of the processed_df corresponds to the 50th row (index 49)
    # of the original dataframe.
    expected_sma = sample_ohlcv_df["Close"].iloc[0:50].mean()
    actual_sma = processed_df["sma50"].iloc[0]

    assert actual_sma == pytest.approx(expected_sma)
