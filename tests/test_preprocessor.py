import pandas as pd
import pytest
import numpy as np

from src.data_preprocessor import preprocess_data


@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    """Creates a sample OHLCV DataFrame with enough data for indicators."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=300))
    data = {
        "Open": np.linspace(100, 200, 300),
        "High": np.linspace(102, 202, 300),
        "Low": np.linspace(98, 198, 300),
        "Close": np.linspace(101, 201, 300),
        "Volume": np.linspace(1000, 2000, 300),
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"
    return df


def test_preprocess_data_adds_columns(sample_ohlcv_df: pd.DataFrame):
    """Tests that preprocess_data adds the expected columns."""
    processed_df = preprocess_data(
        sample_ohlcv_df, sma50_period=50, sma200_period=200, atr_period=14
    )

    assert "sma50" in processed_df.columns
    assert "sma200" in processed_df.columns
    assert "atr14" in processed_df.columns
    assert "pct_change" in processed_df.columns


def test_preprocess_data_removes_nans(sample_ohlcv_df: pd.DataFrame):
    """Tests that no NaN values exist in the processed DataFrame."""
    processed_df = preprocess_data(
        sample_ohlcv_df, sma50_period=50, sma200_period=200, atr_period=14
    )

    assert not processed_df.isnull().values.any()
    # The first 199 rows of the original df should be dropped due to SMA(200) calculation.
    assert len(processed_df) == len(sample_ohlcv_df) - 199


def test_preprocess_data_is_pure(sample_ohlcv_df: pd.DataFrame):
    """Tests that the function does not modify the original DataFrame."""
    original_df_copy = sample_ohlcv_df.copy()
    preprocess_data(sample_ohlcv_df, sma50_period=50, sma200_period=200, atr_period=14)

    pd.testing.assert_frame_equal(original_df_copy, sample_ohlcv_df)


def test_preprocess_data_calculation(sample_ohlcv_df: pd.DataFrame):
    """Performs a sanity check on the first calculated SMA values."""
    processed_df = preprocess_data(
        sample_ohlcv_df, sma50_period=50, sma200_period=200, atr_period=14
    )

    # The first row of the processed_df corresponds to the 200th row (index 199)
    # of the original dataframe.
    expected_sma50 = sample_ohlcv_df["Close"].iloc[150:200].mean()
    expected_sma200 = sample_ohlcv_df["Close"].iloc[0:200].mean()
    actual_sma50 = processed_df["sma50"].iloc[0]
    actual_sma200 = processed_df["sma200"].iloc[0]

    assert actual_sma50 == pytest.approx(expected_sma50)
    assert actual_sma200 == pytest.approx(expected_sma200)


def test_normalization(sample_ohlcv_df: pd.DataFrame):
    """Tests the optional normalization feature."""
    processed_df = preprocess_data(
        sample_ohlcv_df,
        sma50_period=50,
        sma200_period=200,
        atr_period=14,
        normalize_window=True,
    )

    assert "close_norm" in processed_df.columns
    assert "volume_norm" in processed_df.columns
    assert processed_df["close_norm"].min() >= 0
    assert processed_df["close_norm"].max() <= 1
    assert processed_df["volume_norm"].min() >= 0
    assert processed_df["volume_norm"].max() <= 1


def test_atr_with_zero_range(sample_ohlcv_df: pd.DataFrame):
    """Tests ATR calculation when High, Low, and previous Close are identical."""
    df = sample_ohlcv_df.copy()
    # Force a period of no price movement
    df.loc[df.index[10:20], ["High", "Low", "Close"]] = 150
    df.loc[df.index[9], "Close"] = 150

    processed_df = preprocess_data(df, sma50_period=50, sma200_period=200, atr_period=14)
    # This test is primarily to ensure no division-by-zero or other errors occur.
    # A specific value check is less important than ensuring it runs.
    assert "atr14" in processed_df.columns
    assert not processed_df["atr14"].isnull().any()
