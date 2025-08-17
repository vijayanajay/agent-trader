# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd

__all__ = ["score", "ScorerConfig"]


@dataclass
class ScorerConfig:
    """Explicit configuration for the deterministic scorer."""

    return_lookback_days: int = 10
    return_score_max: float = 4.0
    volume_score_max: float = 3.0
    sma_bonus_score: float = 3.0
    volatility_score_max: float = 2.0
    volatility_target_pct_low: float = 1.5
    volatility_target_pct_high: float = 4.0

    @property
    def return_score_scale_factor(self) -> float:
        """Maps a 10% return to the max score."""
        return self.return_score_max / 0.1

    @property
    def volume_score_scale_factor(self) -> float:
        """Maps a 100% volume surge to the max score."""
        return self.volume_score_max / 1.0


def _calculate_return_score(
    df: pd.DataFrame, price: float, cfg: ScorerConfig
) -> Dict[str, Any]:
    """Calculates return score, adjusted for trend consistency."""
    lookback = cfg.return_lookback_days + 1
    if len(df) < lookback:
        return {"return_score": 0.0, "trend_consistency_score": 0.0}

    recent_closes = df["Close"].iloc[-lookback:]
    price_ago = recent_closes.iloc[0]
    return_pct = (price - price_ago) / price_ago if price_ago else 0.0
    raw_score = min(max(0, return_pct * cfg.return_score_scale_factor), cfg.return_score_max)

    up_days = (recent_closes.diff().dropna() > 0).sum()
    consistency = up_days / cfg.return_lookback_days
    return {"return_score": raw_score * consistency, "trend_consistency_score": consistency}


def _calculate_volume_score(df: pd.DataFrame, cfg: ScorerConfig) -> float:
    """Calculates volume surge score."""
    median_vol = df["Volume"].median()
    current_vol = df["Volume"].iloc[-1]
    if median_vol > 0:
        surge = (current_vol / median_vol) - 1.0
        return min(max(0, surge * cfg.volume_score_scale_factor), cfg.volume_score_max)
    return 0.0


def _calculate_volatility_score(
    price: float, atr14: float, return_score: float, cfg: ScorerConfig
) -> float:
    """
    Calculates inverse volatility score, rewarding low ATR.
    Per tested logic, this bonus is only applied if there is positive momentum.
    """
    if return_score <= 0 or price <= 0 or pd.isna(atr14):
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
    current_price: float,
    sma50: float,
    atr14: float,
    config: ScorerConfig = ScorerConfig(),
) -> Dict[str, Any]:
    """
    Scores a data window based on a deterministic, configurable ruleset.

    Args:
        window_df: DataFrame of OHLCV data for the lookback period.
        current_price: The current closing price.
        sma50: The 50-day simple moving average for the current day.
        atr14: The 14-day Average True Range.
        config: A ScorerConfig object with scoring parameters.

    Returns:
        A dictionary containing the score components and a description.
    """
    min_data_len = config.return_lookback_days + 1
    if len(window_df) < min_data_len:
        return {
            "final_score": 0.0, "return_score": 0.0, "volume_score": 0.0,
            "sma_score": 0.0, "volatility_score": 0.0, "trend_consistency_score": 0.0,
            "description": f"Not enough data for {config.return_lookback_days}-day analysis.",
        }

    # --- Calculate Score Components ---
    return_scores = _calculate_return_score(window_df, current_price, config)
    volume_score = _calculate_volume_score(window_df, config)
    sma_score = config.sma_bonus_score if not pd.isna(sma50) and current_price > sma50 else 0.0
    volatility_score = _calculate_volatility_score(
        current_price, atr14, return_scores["return_score"], config
    )

    total_score = round(
        return_scores["return_score"] + volume_score + sma_score + volatility_score, 2
    )

    desc = (
        f"Ret({return_scores['return_score']:.1f}) "
        f"Trend({return_scores['trend_consistency_score']:.2f}) "
        f"Vol({volume_score:.1f}) SMA({sma_score:.1f}) "
        f"Volatility({volatility_score:.1f})"
    )

    return {
        "final_score": total_score,
        "description": desc,
        "return_score": return_scores["return_score"],
        "trend_consistency_score": return_scores["trend_consistency_score"],
        "volume_score": volume_score,
        "sma_score": sma_score,
        "volatility_score": volatility_score,
    }
