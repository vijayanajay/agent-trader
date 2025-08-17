import pandas as pd
import pytest
import subprocess
import sys
import os
from pathlib import Path
from src.analysis.results import analyze_results

@pytest.fixture
def sample_results_mixed() -> pd.DataFrame:
    """Fixture for a mix of winning and losing trades."""
    data = {
        "return_pct": [10, -5, 20, -10, 5],
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_results_all_wins() -> pd.DataFrame:
    """Fixture for only winning trades."""
    data = {
        "return_pct": [10, 20, 5],
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_results_all_losses() -> pd.DataFrame:
    """Fixture for only losing trades."""
    data = {
        "return_pct": [-10, -5, -2],
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_results_no_trades() -> pd.DataFrame:
    """Fixture for an empty DataFrame."""
    return pd.DataFrame({"return_pct": []})

def test_analyze_results_mixed(sample_results_mixed: pd.DataFrame):
    """Test analysis with a mix of wins and losses."""
    metrics = analyze_results(sample_results_mixed)
    assert metrics["total_trades"] == 5
    assert metrics["win_rate"] == 60.0
    assert metrics["profit_factor"] == 2.33  # (10 + 20 + 5) / (5 + 10) = 35 / 15

def test_analyze_results_all_wins(sample_results_all_wins: pd.DataFrame):
    """Test analysis with all winning trades."""
    metrics = analyze_results(sample_results_all_wins)
    assert metrics["total_trades"] == 3
    assert metrics["win_rate"] == 100.0
    assert metrics["profit_factor"] == float("inf")

def test_analyze_results_all_losses(sample_results_all_losses: pd.DataFrame):
    """Test analysis with all losing trades."""
    metrics = analyze_results(sample_results_all_losses)
    assert metrics["total_trades"] == 3
    assert metrics["win_rate"] == 0.0
    assert metrics["profit_factor"] == 0.0

def test_analyze_results_no_trades(sample_results_no_trades: pd.DataFrame):
    """Test analysis with no trades."""
    metrics = analyze_results(sample_results_no_trades)
    assert metrics["total_trades"] == 0
    assert metrics["win_rate"] == 0.0
    assert metrics["profit_factor"] == 0.0

@pytest.fixture
def sample_results_legacy_column() -> pd.DataFrame:
    """Fixture with the legacy 'forward_return_pct' column name."""
    data = {"forward_return_pct": [10, -5, 20]}
    return pd.DataFrame(data)

@pytest.fixture
def sample_results_no_return_col() -> pd.DataFrame:
    """Fixture with no recognizable return column."""
    data = {"some_other_col": [10, -5, 20]}
    return pd.DataFrame(data)

def test_analyze_results_legacy_column_name(sample_results_legacy_column: pd.DataFrame):
    """Tests that the analysis function handles the legacy column name."""
    metrics = analyze_results(sample_results_legacy_column)
    assert metrics["total_trades"] == 3
    assert metrics["win_rate"] == 66.67
    assert metrics["profit_factor"] == 6.0  # (10 + 20) / 5

def test_analyze_results_no_return_column(sample_results_no_return_col: pd.DataFrame):
    """Tests that the analysis function returns zero metrics if no return column is found."""
    metrics = analyze_results(sample_results_no_return_col)
    assert metrics["total_trades"] == 0
    assert metrics["win_rate"] == 0.0
    assert metrics["profit_factor"] == 0.0


# --- CLI Integration Tests ---

ANALYSIS_SCRIPT_PATH = "src/analysis/results.py"

@pytest.fixture
def temp_results_csv(tmp_path: Path) -> str:
    """Creates a temporary results CSV for testing the CLI."""
    csv_path = tmp_path / "temp_results.csv"
    data = {"forward_return_pct": [10, -5, 20, -10, 5]}
    pd.DataFrame(data).to_csv(csv_path, index=False)
    return str(csv_path)


def test_analysis_cli_happy_path(temp_results_csv: str) -> None:
    """Tests the CLI script with a valid CSV file."""
    # Arrange
    command = [sys.executable, ANALYSIS_SCRIPT_PATH, temp_results_csv]

    # Act
    result = subprocess.run(command, capture_output=True, text=True, check=True)

    # Assert: Check for substrings to make the test robust against formatting changes.
    output = result.stdout
    assert "Backtest Performance" in output
    assert "Analysis" in output
    assert "Total Trades" in output
    assert "5" in output
    assert "Win Rate" in output
    assert "60.00" in output
    assert "Profit Factor" in output
    assert "2.33" in output
    assert result.stderr == ""


def test_analysis_cli_file_not_found() -> None:
    """Tests that the CLI script exits gracefully if the file is not found."""
    # Arrange
    command = [sys.executable, ANALYSIS_SCRIPT_PATH, "non_existent_file.csv"]

    # Act
    result = subprocess.run(command, capture_output=True, text=True)

    # Assert
    assert result.returncode != 0
    assert "Error: File not found" in result.stderr
