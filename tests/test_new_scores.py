# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from pathlib import Path
import pandas as pd
import pytest

RESULTS_DIR = Path("results")
RUN_LOG_DIR = RESULTS_DIR / "runs"
SAMPLE_CSV_PATH = "data/ohlcv/RELIANCE.NS.sample.csv"
SAMPLE_TICKER_STEM = Path(SAMPLE_CSV_PATH).stem
SAMPLE_RESULTS_PATH = RESULTS_DIR / f"results_{SAMPLE_TICKER_STEM}.csv"
SAMPLE_RUN_LOG_PATH = RUN_LOG_DIR / f"{SAMPLE_TICKER_STEM}.run_log.csv"


def test_trade_results_include_numeric_scores(tmp_path: Path) -> None:
    """Run backtester and assert trade CSV includes numeric score columns."""
    # cleanup
    if SAMPLE_RESULTS_PATH.exists():
        SAMPLE_RESULTS_PATH.unlink()
    if SAMPLE_RUN_LOG_PATH.exists():
        SAMPLE_RUN_LOG_PATH.unlink()

    cmd = [sys.executable, "backtester.py", "--ticker", SAMPLE_CSV_PATH]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Backtester failed: {res.stderr}"

    assert SAMPLE_RESULTS_PATH.exists(), "results CSV not created"
    df = pd.read_csv(SAMPLE_RESULTS_PATH)

    # New numeric score columns should be present in trade CSV
    for col in [
        "return_score",
        "trend_consistency_score",
        "volume_score",
        "sma_score",
        "volatility_score",
    ]:
        assert col in df.columns, f"{col} missing from trade results"


def test_signal_quality_output_contains_new_features(tmp_path: Path) -> None:
    """Run signal_quality CLI and check generated CSV contains rows for the new features."""
    # Create deterministic small results and log CSVs to drive signal_quality
    results_df = pd.DataFrame(
        {
            "entry_date": ["2023-01-05", "2023-01-10"],
            "outcome": ["TAKE_PROFIT_HIT", "STOP_LOSS_HIT"],
        }
    )
    log_df = pd.DataFrame(
        {
            "date": ["2023-01-05", "2023-01-10", "2023-01-11"],
            "price": [100.0, 105.0, 110.0],
            "atr14": [2.0, 2.5, 3.0],
            "return_score": [1.2, 0.8, 0.5],
            "trend_consistency_score": [0.7, 0.6, 0.5],
            "volume_score": [1.0, 0.5, 0.2],
            "sma_score": [3.0, 3.0, 3.0],
            "volatility_score": [1.1, 1.2, 1.0],
        }
    )

    results_path = tmp_path / "temp_results.csv"
    log_path = tmp_path / "temp_log.csv"
    results_df.to_csv(results_path, index=False)
    log_df.to_csv(log_path, index=False)

    import os as _os
    results_base = _os.path.splitext(_os.path.basename(str(results_path)))[0]
    out_base = Path("results") / f"signal_quality_{results_base}.csv"
    if out_base.exists():
        out_base.unlink()

    cmd = [
        sys.executable,
        "src/analysis/signal_quality.py",
        "--results",
        str(results_path),
        "--log",
        str(log_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"signal_quality failed: {res.stderr}"

    assert out_base.exists(), "signal_quality output CSV not created"
    out_df = pd.read_csv(out_base)

    # The pivot output has a 'feature' column; check the new features are present
    features = set(out_df["feature"].tolist())
    for feat in [
        "return_score",
        "trend_consistency_score",
        "volume_score",
        "sma_score",
        "volatility_score",
    ]:
        assert feat in features, f"{feat} not present in signal_quality output"
