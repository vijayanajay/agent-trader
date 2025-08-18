import pandas as pd
import pytest
from src.analyze_results import analyze_results

@pytest.fixture
def sample_results_mixed() -> pd.DataFrame:
    """Fixture for a mix of winning and losing trades."""
    data = {
        "forward_return_pct": [10, -5, 20, -10, 5],
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_results_all_wins() -> pd.DataFrame:
    """Fixture for only winning trades."""
    data = {
        "forward_return_pct": [10, 20, 5],
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_results_all_losses() -> pd.DataFrame:
    """Fixture for only losing trades."""
    data = {
        "forward_return_pct": [-10, -5, -2],
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_results_no_trades() -> pd.DataFrame:
    """Fixture for an empty DataFrame."""
    return pd.DataFrame({"forward_return_pct": []})

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
