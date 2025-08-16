import pandas as pd
from typing import Dict

__all__ = ["score_pattern_deterministically"]


def score_pattern_deterministically(window_data: pd.DataFrame) -> Dict[str, float]:
    """
    Scores a 40-day data window based on deterministic rules.

    The score is based on two factors:
    1.  Momentum Score (0-5): Based on the 20-day price change.
    2.  Volume Surge Score (0-5): Based on recent volume compared to average.

    Args:
        window_data: A 40-day DataFrame of OHLCV data.

    Returns:
        A dictionary containing the total score and sub-scores.
    """
    # --- 1. Momentum Score (0-5 points) ---
    # Compare the most recent price to the price 20 days ago
    price_now = window_data["Close"].iloc[-1]
    price_20d_ago = window_data["Close"].iloc[-21]

    momentum_pct = (price_now - price_20d_ago) / price_20d_ago if price_20d_ago != 0 else 0

    # Scale the momentum percentage to a score of 0-5.
    # A 10% increase over 20 days maps to a score of 5.
    momentum_score = min(max(0, momentum_pct * 50), 5)

    # --- 2. Volume Surge Score (0-5 points) ---
    # Compare the average volume of the last 5 days to the average of the whole window
    avg_volume_total = window_data["Volume"].mean()
    avg_volume_last_5d = window_data["Volume"].tail(5).mean()

    volume_ratio = avg_volume_last_5d / avg_volume_total if avg_volume_total > 0 else 1

    # Scale the volume ratio to a score of 0-5.
    # A ratio of 2.0 (i.e., 100% increase) maps to a score of 5.
    volume_score = min(max(0, (volume_ratio - 1) * 5), 5)

    # --- 3. Final Score ---
    total_score = round(momentum_score + volume_score, 2)

    return {
        "pattern_score": total_score,
        "momentum_score": round(momentum_score, 2),
        "volume_score": round(volume_score, 2),
    }
