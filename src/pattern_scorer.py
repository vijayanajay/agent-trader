# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd

__all__ = ["score", "ScorerConfig"]


@dataclass
class ScorerConfig:
    """Explicit configuration for the deterministic scorer."""

    relative_strength_lookback_days: int = 10
    relative_strength_score_max: float = 4.0
    volume_score_max: float = 3.0
    sma_bonus_score: float = 3.0
    volatility_score_max: float = 2.0
    volatility_target_pct_low: float = 1.5
    volatility_target_pct_high: float = 4.0

    @property
    def relative_strength_score_scale_factor(self) -> float:
        """Maps a 5% relative outperformance to the max score."""
        return self.relative_strength_score_max / 0.05

    @property
    def volume_score_scale_factor(self) -> float:
        """Maps a 100% volume surge to the max score."""
        return self.volume_score_max / 1.0


def _calculate_relative_strength_score(
    stock_df: pd.DataFrame, market_df: pd.DataFrame, cfg: ScorerConfig
) -> float:
    """Calculates the relative strength score."""
    lookback = cfg.relative_strength_lookback_days + 1
    if len(stock_df) < lookback or market_df.empty or len(market_df) < lookback:
        return 0.0

    stock_price_now = stock_df["Close"].iloc[-1]
    stock_price_ago = stock_df["Close"].iloc[-lookback]
    stock_return = (stock_price_now - stock_price_ago) / stock_price_ago if stock_price_ago else 0.0

    market_price_now = market_df["Close"].iloc[-1]
    market_price_ago = market_df["Close"].iloc[-lookback]
    market_return = (market_price_now - market_price_ago) / market_price_ago if market_price_ago else 0.0

    relative_return = stock_return - market_return
    score = relative_return * cfg.relative_strength_score_scale_factor
    return float(min(max(0, score), cfg.relative_strength_score_max))


def _calculate_volume_score(df: pd.DataFrame, cfg: ScorerConfig) -> float:
    """Calculates volume surge score."""
    median_vol = df["Volume"].median()
    current_vol = df["Volume"].iloc[-1]
    if median_vol > 0:
        surge = (current_vol / median_vol) - 1.0
        return min(max(0, surge * cfg.volume_score_scale_factor), cfg.volume_score_max)
    return 0.0


def _calculate_volatility_score(
    price: float, atr14: float, relative_strength_score: float, cfg: ScorerConfig
) -> float:
    """
    Calculates inverse volatility score, rewarding low ATR.
    Per tested logic, this bonus is only applied if there is positive momentum.
    """
    if relative_strength_score <= 0 or price <= 0 or pd.isna(atr14):
        return 0.0

    atr_pct = (atr14 / price) * 100
    if atr_pct <= cfg.volatility_target_pct_low:
        return cfg.volatility_score_max
    if atr_pct >= cfg.volatility_target_pct_high:
        return 0.0

    vol_range = cfg.volatility_target_pct_high - cfg.volatility_target_pct_low
    if vol_range <= 0:
        return 0.0
    return cfg.volatility_score_max * ((cfg.volatility_target_pct_high - atr_pct) / vol_range)


def score(
    window_df: pd.DataFrame,
    market_window_df: pd.DataFrame,
    current_price: float,
    sma50: float,
    atr14: float,
    config: ScorerConfig = ScorerConfig(),
) -> Dict[str, Any]:
    """
    Scores a data window based on a deterministic, configurable ruleset.

    Args:
        window_df: DataFrame of OHLCV data for the lookback period.
        market_window_df: DataFrame of market index data for the lookback period.
        current_price: The current closing price.
        sma50: The 50-day simple moving average for the current day.
        atr14: The 14-day Average True Range.
        config: A ScorerConfig object with scoring parameters.

    Returns:
        A dictionary containing the score components and a description.
    """
    min_data_len = config.relative_strength_lookback_days + 1
    if len(window_df) < min_data_len:
        return {
            "final_score": 0.0, "relative_strength_score": 0.0, "volume_score": 0.0,
            "sma_score": 0.0, "volatility_score": 0.0,
            "description": f"Not enough data for {config.relative_strength_lookback_days}-day analysis.",
        }

    # --- Calculate Score Components ---
    relative_strength_score = _calculate_relative_strength_score(window_df, market_window_df, config)
    volume_score = _calculate_volume_score(window_df, config)
    sma_score = config.sma_bonus_score if not pd.isna(sma50) and current_price > sma50 else 0.0
    volatility_score = _calculate_volatility_score(
        current_price, atr14, relative_strength_score, config
    )

    total_score = round(
        relative_strength_score + volume_score + sma_score + volatility_score, 2
    )

    desc = (
        f"RS({relative_strength_score:.1f}) "
        f"Vol({volume_score:.1f}) SMA({sma_score:.1f}) "
        f"Volatility({volatility_score:.1f})"
    )

    return {
        "final_score": total_score,
        "description": desc,
        "relative_strength_score": relative_strength_score,
        "volume_score": volume_score,
        "sma_score": sma_score,
        "volatility_score": volatility_score,
    }
