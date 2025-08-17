# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from pathlib import Path
from typing import Generator, cast
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from backtester import BacktestConfig, run_backtest
from src.pattern_scorer import ScorerConfig

# --- Test Configuration ---
SAMPLE_CSV_PATH = "data/ohlcv/RELIANCE.NS.sample.csv"
BACKTESTER_SCRIPT_PATH = "backtester.py"


# --- Test Derived Paths ---
RESULTS_DIR = Path("results")
RUN_LOG_DIR = RESULTS_DIR / "runs"

# Path for the main test using the sample file
SAMPLE_TICKER_STEM = Path(SAMPLE_CSV_PATH).stem
SAMPLE_RESULTS_PATH = RESULTS_DIR / f"results_{SAMPLE_TICKER_STEM}.csv"
SAMPLE_RUN_LOG_PATH = RUN_LOG_DIR / f"{SAMPLE_TICKER_STEM}.run_log.csv"

# Store a reference to the real pandas.read_csv before it gets mocked
# This is crucial to avoid recursion errors in the mock's side_effect.
REAL_PANDAS_READ_CSV = pd.read_csv


@pytest.fixture(autouse=True)
def cleanup_results_files() -> Generator[None, None, None]:
    """Ensure results files are clean before and after each test."""
    files_to_remove = [SAMPLE_RESULTS_PATH, SAMPLE_RUN_LOG_PATH]
    for f in files_to_remove:
        if f.exists():
            f.unlink()

    yield

    for f in files_to_remove:
        if f.exists():
            f.unlink()


def test_backtester_happy_path_creates_outputs() -> None:
    """
    Tests that the backtester runs with sample data and creates both the
    main trade results CSV and the detailed daily run log.
    """
    command = [
        sys.executable,
        BACKTESTER_SCRIPT_PATH,
        "--ticker",
        SAMPLE_CSV_PATH,
    ]

    # Act
    result = subprocess.run(command, capture_output=True, text=True)

    # Assert
    assert result.returncode == 0, f"Backtester script failed with error:\n{result.stderr}"

    # 1. Verify trade results file
    assert SAMPLE_RESULTS_PATH.exists(), "Trade results CSV was not created."
    results_df = pd.read_csv(SAMPLE_RESULTS_PATH)
    assert results_df is not None, "Failed to read trade results CSV."
    expected_trade_cols = [
        "entry_date", "entry_price", "pattern_score", "pattern_desc",
        "stop_loss", "take_profit", "outcome", "forward_return_pct"
    ]
    assert all(col in results_df.columns for col in expected_trade_cols)

    # 2. Verify daily run log file
    assert SAMPLE_RUN_LOG_PATH.exists(), "Daily run log CSV was not created."
    log_df = pd.read_csv(SAMPLE_RUN_LOG_PATH)
    assert log_df is not None, "Failed to read run log CSV."
    expected_log_cols = [
        "date", "price", "atr14", "sma50", "final_score",
        "return_score", "volume_score", "sma_score", "volatility_score",
        "trend_consistency_score", "description"
    ]
    # The log can be empty if the market regime filter skips all days
    if not log_df.empty:
        assert all(col in log_df.columns for col in expected_log_cols)


def test_backtester_no_data_creates_empty_results_csv() -> None:
    """
    Tests that the backtester handles a file with insufficient data gracefully
    and creates an empty results file with only headers.
    """
    # Arrange: Create a temporary CSV with too few rows
    temp_csv_path = "tests/temp_short_data.csv"
    sample_df = pd.read_csv(SAMPLE_CSV_PATH)
    short_df = sample_df.head(50)
    short_df.to_csv(temp_csv_path, index=False)

    command = [
        sys.executable,
        BACKTESTER_SCRIPT_PATH,
        "--ticker",
        temp_csv_path,
    ]

    # Act
    result = subprocess.run(command, capture_output=True, text=True)

    # Assert
    assert result.returncode == 0, f"Backtester script failed with error:\n{result.stderr}"

    temp_ticker_stem = Path(temp_csv_path).stem
    results_path = RESULTS_DIR / f"results_{temp_ticker_stem}.csv"

    assert results_path.exists(), "Results CSV file was not created for the no-data case."

    results_df = pd.read_csv(results_path)
    assert results_df.empty, "Results CSV should be empty for insufficient data."

    # Cleanup the temporary file
    os.remove(temp_csv_path)
    if results_path.exists():
        os.remove(results_path)


def _create_mock_nifty_data(base_df: pd.DataFrame, trend: str) -> pd.DataFrame:
    """Creates a mock NIFTY DataFrame with a specific trend."""
    nifty_df = pd.DataFrame(index=base_df.index)
    if trend == "up":
        # Price is always above SMA200
        nifty_df["Close"] = 20000
        nifty_df["sma200"] = 19000
    elif trend == "down":
        # Price is always below SMA200
        nifty_df["Close"] = 18000
        nifty_df["sma200"] = 19000
    return nifty_df


@pytest.mark.parametrize(
    "market_trend, expect_trades",
    [
        ("up", True),
        ("down", False),
    ],
)
@patch("pandas.read_csv")
def test_backtester_market_regime_filter(
    mock_read_csv: MagicMock, market_trend: str, expect_trades: bool
) -> None:
    """
    Tests the market regime filter by mocking pandas.read_csv.
    """
    # Arrange
    sample_df = REAL_PANDAS_READ_CSV(SAMPLE_CSV_PATH, index_col="Date", parse_dates=True)
    mock_nifty_df = _create_mock_nifty_data(sample_df, market_trend)

    from typing import Any
    def read_csv_side_effect(filepath: str, *args: Any, **kwargs: Any) -> pd.DataFrame:
        # If the backtester asks for the NIFTY CSV, return our mock.
        if Path(filepath).name == "^NSEI.csv":
            return mock_nifty_df
        # Otherwise, call the real read_csv for the actual ticker data.
        # The return type of read_csv can be a TextFileReader, but we know it's a DataFrame here.
        return cast(pd.DataFrame, REAL_PANDAS_READ_CSV(filepath, *args, **kwargs))

    mock_read_csv.side_effect = read_csv_side_effect

    # Act
    bt_config = BacktestConfig(lookback_window=40)
    scorer_config = ScorerConfig()
    trades, daily_logs = run_backtest(
        csv_path=SAMPLE_CSV_PATH, cfg=bt_config, scorer_cfg=scorer_config
    )

    # Assert
    if expect_trades:
        # In an uptrend, we expect the backtester to process days, so logs should exist.
        # We don't assert that trades must be found, as that depends on the scorer.
        assert len(daily_logs) > 0, "Should have processed days in an uptrend market."
    else:
        # In a downtrend, the filter should skip all days, resulting in no logs or trades.
        assert len(daily_logs) == 0, "Should not have processed any days in a downtrend."
        assert len(trades) == 0, "Should not have found trades in a downtrend market."
