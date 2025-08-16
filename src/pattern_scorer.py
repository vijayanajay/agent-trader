# -*- coding: utf-8 -*-
from typing import Any, Dict

import pandas as pd

__all__ = ["score"]


def score(
    window_df: pd.DataFrame, current_price: float, sma50: float
) -> Dict[str, Any]:
    """
    Scores a 40-day data window based on deterministic rules from Task 4.

    Components:
    1.  Recent 10-day return (scaled, 0-4 points).
    2.  Volume surge (current vs median, 0-3 points).
    3.  Position vs sma50 (above => bonus, 3 points).

    Args:
        window_df: A 40-day DataFrame of OHLCV data.
        current_price: The current closing price.
        sma50: The 50-day simple moving average for the current day.

    Returns:
        A dictionary containing the score and a description.
    """
    # 1. Return Score (0-4 points)
    # Ensure there are at least 11 days for a 10-day lookback.
    if len(window_df) < 11:
        return {
            "pattern_strength_score": 0.0,
            "pattern_description": "Not enough data for 10-day return.",
        }
    price_10d_ago = window_df["Close"].iloc[-11]
    return_pct = (
        (current_price - price_10d_ago) / price_10d_ago if price_10d_ago else 0
    )
    # A 10% gain maps to 4 points. Clamp between 0 and 4.
    return_score = min(max(0, return_pct * 40), 4)

    # 2. Volume Surge Score (0-3 points)
    median_volume = window_df["Volume"].median()
    current_volume = window_df["Volume"].iloc[-1]
    volume_score = 0.0
    if median_volume > 0:
        volume_ratio = current_volume / median_volume
        # A 100% surge (ratio of 2.0) maps to 3 points. Clamp between 0 and 3.
        volume_score = min(max(0, (volume_ratio - 1) * 3), 3)

    # 3. SMA Bonus (3 points)
    sma_score = 3.0 if not pd.isna(sma50) and current_price > sma50 else 0.0

    total_score = round(return_score + volume_score + sma_score, 2)

    desc = (
        f"Return({return_score:.1f}/4), "
        f"Volume({volume_score:.1f}/3), "
        f"SMA({sma_score:.1f}/3)"
    )

    return {
        "pattern_strength_score": total_score,
        "pattern_description": desc,
    }
