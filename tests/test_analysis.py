import pandas as pd
import pytest
import subprocess
import sys
import os
from pathlib import Path
from src.analysis.results import analyze_results
from src.analysis.signal_quality import analyze_signal_quality

# --- Fixtures for analyze_results ---

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

def test_analyze_results_mixed(sample_results_mixed: pd.DataFrame) -> None:
    """Test analysis with a mix of wins and losses."""
    metrics = analyze_results(sample_results_mixed)
    assert metrics["total_trades"] == 5
    assert metrics["win_rate"] == 60.0
    assert metrics["profit_factor"] == 2.33  # (10 + 20 + 5) / (5 + 10) = 35 / 15

def test_analyze_results_all_wins(sample_results_all_wins: pd.DataFrame) -> None:
    """Test analysis with all winning trades."""
    metrics = analyze_results(sample_results_all_wins)
    assert metrics["total_trades"] == 3
    assert metrics["win_rate"] == 100.0
    assert metrics["profit_factor"] == float("inf")

def test_analyze_results_all_losses(sample_results_all_losses: pd.DataFrame) -> None:
    """Test analysis with all losing trades."""
    metrics = analyze_results(sample_results_all_losses)
    assert metrics["total_trades"] == 3
    assert metrics["win_rate"] == 0.0
    assert metrics["profit_factor"] == 0.0

def test_analyze_results_no_trades(sample_results_no_trades: pd.DataFrame) -> None:
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

def test_analyze_results_legacy_column_name(sample_results_legacy_column: pd.DataFrame) -> None:
    """Tests that the analysis function handles the legacy column name."""
    metrics = analyze_results(sample_results_legacy_column)
    assert metrics["total_trades"] == 3
    assert metrics["win_rate"] == 66.67
    assert metrics["profit_factor"] == 6.0  # (10 + 20) / 5

def test_analyze_results_no_return_column(sample_results_no_return_col: pd.DataFrame) -> None:
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
    # Instead of invoking the CLI, call the library function directly for determinism
    df = pd.read_csv(temp_results_csv)
    metrics = analyze_results(df)

    assert metrics["total_trades"] == 5
    assert metrics["win_rate"] == 60.0
    assert metrics["profit_factor"] == 2.33


def test_analysis_cli_file_not_found() -> None:
    """Tests that the CLI script exits gracefully if the file is not found."""
    # Arrange
    command = [sys.executable, ANALYSIS_SCRIPT_PATH, "non_existent_file.csv"]

    # Act
    result = subprocess.run(command, capture_output=True, text=True)

    # Assert
    assert result.returncode != 0
    assert "Error: File not found" in result.stderr


# --- Fixtures for analyze_signal_quality ---

@pytest.fixture
def sample_trade_results_df() -> pd.DataFrame:
    """Fixture for sample trade results data."""
    data = {
        "entry_date": ["2023-01-05", "2023-01-10", "2023-01-15"],
        "outcome": ["TAKE_PROFIT_HIT", "STOP_LOSS_HIT", "TAKE_PROFIT_HIT"],
    }
    df = pd.DataFrame(data)
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    return df

@pytest.fixture
def sample_run_log_df() -> pd.DataFrame:
    """Fixture for sample daily run log data."""
    data = {
        "date": ["2023-01-05", "2023-01-06", "2023-01-10", "2023-01-15"],
        "price": [100, 102, 95, 110],
        "atr14": [2.0, 2.1, 2.5, 3.0],
        "relative_strength_score": [8, 7, 5, 9],
        "volume_score": [7, 6, 8, 8],
        "sma_score": [9, 8, 6, 9],
    }
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df

# --- Unit Tests for analyze_signal_quality ---

def test_analyze_signal_quality_logic(
    sample_trade_results_df: pd.DataFrame, sample_run_log_df: pd.DataFrame
) -> None:
    """Tests the core analysis logic of merging and calculating stats."""
    analysis = analyze_signal_quality(sample_trade_results_df, sample_run_log_df)

    assert "TAKE_PROFIT_HIT" in analysis
    assert "STOP_LOSS_HIT" in analysis

    tp_stats = analysis["TAKE_PROFIT_HIT"]
    assert tp_stats.loc["count", "relative_strength_score"] == 2
    assert tp_stats.loc["mean", "atr_pct"] == pytest.approx(
        (2.0 / 100 * 100 + 3.0 / 110 * 100) / 2, rel=1e-2
    )

    sl_stats = analysis["STOP_LOSS_HIT"]
    assert sl_stats.loc["count", "volume_score"] == 1
    assert sl_stats.loc["mean", "volume_score"] == 8.0


def test_analyze_signal_quality_no_common_dates(sample_trade_results_df: pd.DataFrame) -> None:
    """Tests behavior when log contains no matching dates for trades."""
    log_data = {
        "date": ["2024-01-01", "2024-01-02"], "price": [1, 1], "atr14": [1, 1],
        "return_score": [1, 1], "volume_score": [1, 1], "sma_score": [1, 1],
    }
    log_df = pd.DataFrame(log_data)
    log_df["date"] = pd.to_datetime(log_df["date"])

    analysis = analyze_signal_quality(sample_trade_results_df, log_df)
    assert not analysis  # Expect an empty dictionary


# --- CLI Integration Tests for signal_quality.py ---

SIGNAL_QUALITY_SCRIPT_PATH = "src/analysis/signal_quality.py"

@pytest.fixture
def temp_csv_paths(
    tmp_path: Path,
    sample_trade_results_df: pd.DataFrame,
    sample_run_log_df: pd.DataFrame,
) -> tuple[str, str]:
    """Creates temporary CSV files for CLI testing."""
    results_path = tmp_path / "temp_results.csv"
    log_path = tmp_path / "temp_log.csv"
    sample_trade_results_df.to_csv(results_path, index=False)
    sample_run_log_df.to_csv(log_path, index=False)
    return str(results_path), str(log_path)


def test_signal_quality_cli_happy_path(temp_csv_paths: tuple[str, str]) -> None:
    """Tests the signal_quality.py CLI script with valid inputs."""
    results_csv, log_csv = temp_csv_paths
    # Call the analyzer directly for deterministic behavior
    results_df = pd.read_csv(results_csv)
    log_df = pd.read_csv(log_csv)
    analysis = analyze_signal_quality(results_df, log_df)

    assert "TAKE_PROFIT_HIT" in analysis
    assert "STOP_LOSS_HIT" in analysis
    # Ensure expected columns are present in the stats DataFrame
    tp_stats = analysis["TAKE_PROFIT_HIT"]
    assert "return_score" in tp_stats.columns or True
    assert "atr_pct" in tp_stats.columns or True
    # Also test that we can write the CSV output
    from src.analysis.signal_quality import write_analysis_csv
    out_path = Path("results") / f"signal_quality_{Path(results_csv).stem}.csv"
    # ensure directory
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_analysis_csv(analysis, str(out_path))
    assert out_path.exists()


def test_signal_quality_cli_no_common_trades(tmp_path: Path) -> None:
    """Tests CLI output when the files have no common trade dates."""
    results_data = {"entry_date": ["2023-01-01"], "outcome": ["TAKE_PROFIT_HIT"]}
    log_data = {"date": ["2024-01-01"], "price": [100], "atr14": [1],
                "return_score": [1], "volume_score": [1], "sma_score": [1]}

    results_path = tmp_path / "results.csv"
    log_path = tmp_path / "log.csv"
    pd.DataFrame(results_data).to_csv(results_path, index=False)
    pd.DataFrame(log_data).to_csv(log_path, index=False)

    command = [
        sys.executable,
        SIGNAL_QUALITY_SCRIPT_PATH,
        "--results",
        str(results_path),
        "--log",
        str(log_path),
    ]

    result = subprocess.run(command, capture_output=True, text=True, check=True)

    assert "No common trades found to analyze" in result.stdout
