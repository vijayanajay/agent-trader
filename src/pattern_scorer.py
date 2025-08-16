# -*- coding: utf-8 -*-
from typing import Any, Dict

import pandas as pd

__all__ = ["score"]

# --- Scoring Configuration ---
# Component weights
RETURN_SCORE_MAX = 4.0
VOLUME_SCORE_MAX = 3.0
SMA_BONUS_SCORE = 3.0

# Logic parameters
RETURN_LOOKBACK_DAYS = 10
# A 10% return (0.1) should map to a full score. Scale factor = 4.0 / 0.1 = 40.0
RETURN_SCORE_SCALE_FACTOR = RETURN_SCORE_MAX / 0.1
# A 100% volume surge (ratio of 2.0) should map to a full score.
# Scale factor = 3.0 / (2.0 - 1.0) = 3.0
VOLUME_SCORE_SCALE_FACTOR = VOLUME_SCORE_MAX / 1.0
# --- End Scoring Configuration ---


def score(
    window_df: pd.DataFrame, current_price: float, sma50: float
) -> Dict[str, Any]:
    """
    Scores a data window based on deterministic rules.

    Components:
    1. Recent return (scaled, 0-4 points).
    2. Volume surge (current vs median, 0-3 points).
    3. Position vs sma50 (above => bonus, 3 points).

    Args:
        window_df: DataFrame of OHLCV data for the lookback period.
        current_price: The current closing price.
        sma50: The 50-day simple moving average for the current day.

    Returns:
        A dictionary containing the score and a description.
    """
    # 1. Return Score
    lookback_period = RETURN_LOOKBACK_DAYS + 1  # Need N+1 days for N-day return
    if len(window_df) < lookback_period:
        return {
            "pattern_strength_score": 0.0,
            "pattern_description": f"Not enough data for {RETURN_LOOKBACK_DAYS}-day return.",
        }
    price_n_days_ago = window_df["Close"].iloc[-lookback_period]
    return_pct = (
        (current_price - price_n_days_ago) / price_n_days_ago
        if price_n_days_ago
        else 0
    )
    return_score = min(
        max(0, return_pct * RETURN_SCORE_SCALE_FACTOR), RETURN_SCORE_MAX
    )

    # 2. Volume Surge Score
    median_volume = window_df["Volume"].median()
    current_volume = window_df["Volume"].iloc[-1]
    volume_score = 0.0
    if median_volume > 0:
        volume_ratio = current_volume / median_volume
        # Score is based on the increase over the median (ratio - 1)
        surge_factor = volume_ratio - 1
        volume_score = min(
            max(0, surge_factor * VOLUME_SCORE_SCALE_FACTOR), VOLUME_SCORE_MAX
        )

    # 3. SMA Bonus
    sma_score = SMA_BONUS_SCORE if not pd.isna(sma50) and current_price > sma50 else 0.0

    total_score = round(return_score + volume_score + sma_score, 2)

    desc = (
        f"Return({return_score:.1f}/{RETURN_SCORE_MAX:.0f}), "
        f"Volume({volume_score:.1f}/{VOLUME_SCORE_MAX:.0f}), "
        f"SMA({sma_score:.1f}/{SMA_BONUS_SCORE:.0f})"
    )

    return {
        "pattern_strength_score": total_score,
        "pattern_description": desc,
    }
