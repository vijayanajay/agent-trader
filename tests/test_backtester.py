# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from pathlib import Path
from typing import Generator

import pandas as pd
import pytest

# --- Test Configuration ---
SAMPLE_CSV_PATH = "data/ohlcv/RELIANCE.NS.sample.csv"
RESULTS_CSV_PATH = "results/results.csv"
BACKTESTER_SCRIPT_PATH = "backtester.py"


# --- Test Derived Paths ---
RUN_LOG_DIR = Path("results/runs")
SAMPLE_TICKER_STEM = Path(SAMPLE_CSV_PATH).stem
RUN_LOG_PATH = RUN_LOG_DIR / f"{SAMPLE_TICKER_STEM}.run_log.csv"


@pytest.fixture(autouse=True)
def cleanup_results_files() -> Generator[None, None, None]:
    """Ensure results files are clean before and after each test."""
    if os.path.exists(RESULTS_CSV_PATH):
        os.remove(RESULTS_CSV_PATH)
    if os.path.exists(RUN_LOG_PATH):
        os.remove(RUN_LOG_PATH)
    if os.path.exists(RUN_LOG_DIR) and not os.listdir(RUN_LOG_DIR):
        os.rmdir(RUN_LOG_DIR)
    yield
    if os.path.exists(RESULTS_CSV_PATH):
        os.remove(RESULTS_CSV_PATH)
    if os.path.exists(RUN_LOG_PATH):
        os.remove(RUN_LOG_PATH)
    if os.path.exists(RUN_LOG_DIR) and not os.listdir(RUN_LOG_DIR):
        os.rmdir(RUN_LOG_DIR)


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

    # 1. Verify trade results file (`results.csv`)
    assert Path(RESULTS_CSV_PATH).exists(), "Trade results CSV was not created."
    results_df = pd.read_csv(RESULTS_CSV_PATH)
    assert results_df is not None, "Failed to read trade results CSV."
    expected_trade_cols = [
        "entry_date", "entry_price", "pattern_score", "pattern_desc",
        "stop_loss", "take_profit", "outcome", "forward_return_pct"
    ]
    assert all(col in results_df.columns for col in expected_trade_cols)

    # 2. Verify daily run log file (`...run_log.csv`)
    assert RUN_LOG_PATH.exists(), "Daily run log CSV was not created."
    log_df = pd.read_csv(RUN_LOG_PATH)
    assert not log_df.empty, "Run log CSV is empty."
    expected_log_cols = [
        "date", "price", "atr14", "sma50", "final_score",
        "return_score", "volume_score", "sma_score", "description"
    ]
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
    assert Path(RESULTS_CSV_PATH).exists(), "Results CSV file was not created for the no-data case."

    results_df = pd.read_csv(RESULTS_CSV_PATH)
    assert results_df.empty, "Results CSV should be empty for insufficient data."

    # Cleanup the temporary file
    os.remove(temp_csv_path)
