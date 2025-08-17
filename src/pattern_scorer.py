# -*- coding: utf-8 -*-
from typing import Any, Dict

import pandas as pd

__all__ = ["score"]

# --- Scoring Configuration ---
# Component weights
RETURN_SCORE_MAX = 4.0
VOLUME_SCORE_MAX = 3.0
SMA_BONUS_SCORE = 3.0
VOLATILITY_SCORE_MAX = 2.0

# Logic parameters
RETURN_LOOKBACK_DAYS = 10
RETURN_SCORE_SCALE_FACTOR = RETURN_SCORE_MAX / 0.1  # 10% return maps to max score
VOLUME_SCORE_SCALE_FACTOR = VOLUME_SCORE_MAX / 1.0  # 100% surge maps to max score

# Volatility parameters (lower is better)
VOLATILITY_TARGET_PCT_LOW = 1.5  # ATR% below this gets max score
VOLATILITY_TARGET_PCT_HIGH = 4.0  # ATR% above this gets zero score
# --- End Scoring Configuration ---


def score(
    window_df: pd.DataFrame, current_price: float, sma50: float, atr14: float
) -> Dict[str, Any]:
    """
    Scores a data window based on deterministic rules.

    Components:
    1. Recent return, adjusted for trend consistency (0-4 points).
    2. Volume surge (0-3 points).
    3. Position vs sma50 (3 points bonus).
    4. Inverse volatility (low ATR% gets 0-2 points bonus).

    Args:
        window_df: DataFrame of OHLCV data for the lookback period.
        current_price: The current closing price.
        sma50: The 50-day simple moving average for the current day.
        atr14: The 14-day Average True Range.

    Returns:
        A dictionary containing the score components and a description.
    """
    # 1. Return and Trend Quality Score
    lookback_period = RETURN_LOOKBACK_DAYS + 1
    if len(window_df) < lookback_period:
        return {
            "final_score": 0.0, "return_score": 0.0, "volume_score": 0.0, "sma_score": 0.0,
            "volatility_score": 0.0, "trend_consistency_score": 0.0,
            "description": f"Not enough data for {RETURN_LOOKBACK_DAYS}-day analysis.",
        }

    recent_closes = window_df["Close"].iloc[-lookback_period:]
    price_n_days_ago = recent_closes.iloc[0]
    return_pct = (current_price - price_n_days_ago) / price_n_days_ago if price_n_days_ago else 0
    raw_return_score = min(max(0, return_pct * RETURN_SCORE_SCALE_FACTOR), RETURN_SCORE_MAX)

    # Penalize volatile trends by rewarding consistency.
    up_days = (pd.to_numeric(recent_closes.diff().dropna()) > 0).sum()
    trend_consistency_score = up_days / RETURN_LOOKBACK_DAYS
    return_score = raw_return_score * trend_consistency_score

    # 2. Volume Surge Score
    median_volume = window_df["Volume"].median()
    current_volume = window_df["Volume"].iloc[-1]
    volume_score = 0.0
    if median_volume > 0:
        surge_factor = (current_volume / median_volume) - 1
        volume_score = min(max(0, surge_factor * VOLUME_SCORE_SCALE_FACTOR), VOLUME_SCORE_MAX)

    # 3. SMA Bonus
    sma_score = SMA_BONUS_SCORE if not pd.isna(sma50) and current_price > sma50 else 0.0

    # 4. Volatility Score (Inverse relationship)
    volatility_score = 0.0
    # Only award volatility bonus if there is positive momentum.
    if return_score > 0 and current_price > 0 and not pd.isna(atr14):
        atr_pct = (atr14 / current_price) * 100
        if atr_pct <= VOLATILITY_TARGET_PCT_LOW:
            volatility_score = VOLATILITY_SCORE_MAX
        elif atr_pct < VOLATILITY_TARGET_PCT_HIGH:
            volatility_range = VOLATILITY_TARGET_PCT_HIGH - VOLATILITY_TARGET_PCT_LOW
            volatility_score = VOLATILITY_SCORE_MAX * (
                (VOLATILITY_TARGET_PCT_HIGH - atr_pct) / volatility_range
            )

    total_score = round(return_score + volume_score + sma_score + volatility_score, 2)

    desc = (
        f"Ret({return_score:.1f}) Trend({trend_consistency_score:.2f}) "
        f"Vol({volume_score:.1f}) SMA({sma_score:.1f}) Volatility({volatility_score:.1f})"
    )

    return {
        "final_score": total_score,
        "return_score": return_score,
        "volume_score": volume_score,
        "sma_score": sma_score,
        "volatility_score": volatility_score,
        "trend_consistency_score": trend_consistency_score,
        "description": desc,
    }
