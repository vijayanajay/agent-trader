# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

# --- Test Configuration ---
SAMPLE_CSV_PATH = "data/ohlcv/RELIANCE.NS.sample.csv"
RESULTS_CSV_PATH = "results/results.csv"
BACKTESTER_SCRIPT_PATH = "backtester.py"


@pytest.fixture(autouse=True)
def cleanup_results_file():
    """Ensure the results file is clean before and after each test."""
    if os.path.exists(RESULTS_CSV_PATH):
        os.remove(RESULTS_CSV_PATH)
    yield
    if os.path.exists(RESULTS_CSV_PATH):
        os.remove(RESULTS_CSV_PATH)


def test_backtester_happy_path_creates_results_csv():
    """
    Tests that the backtester runs successfully with the sample data
    and creates a non-empty results file.
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
    assert Path(RESULTS_CSV_PATH).exists(), "Results CSV file was not created."

    results_df = pd.read_csv(RESULTS_CSV_PATH)
    # The sample data may or may not produce trades.
    # The critical part is that the script runs and produces a valid CSV.
    assert results_df is not None, "Failed to read results CSV."

    # Check for expected columns, even if there are no rows.
    expected_columns = [
        "entry_date", "entry_price", "pattern_score", "pattern_desc",
        "stop_loss", "take_profit", "outcome", "forward_return_pct"
    ]
    assert all(col in results_df.columns for col in expected_columns)


def test_backtester_no_data_creates_empty_results_csv():
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
