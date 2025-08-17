# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import pytest
from typing import List

from src.pattern_scorer import score, ScorerConfig


def _create_synthetic_data(
    prices: List[float], volumes: List[int]
) -> pd.DataFrame:
    """Creates a DataFrame from lists of prices and volumes for testing."""
    if not prices:
        return pd.DataFrame({"Close": [], "Volume": []})
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=len(prices)))
    return pd.DataFrame({"Close": prices, "Volume": volumes}, index=dates)


def test_score_bullish_scenario() -> None:
    """
    Tests the scorer with a synthetic bullish window.
    - Strong relative strength, high volume, price > sma50, moderate volatility.
    Expected score should be high.
    """
    # Arrange: Create a bullish window (40 days)
    prices = [100 + i * 0.5 for i in range(30)] + [115 + i for i in range(10)]
    volumes = [1000] * 35 + [3000] * 5  # Volume surge at the end
    window_df = _create_synthetic_data(prices, volumes)
    # Market is flat, so all stock return is relative strength
    market_prices = [100.0] * 40
    market_window_df = _create_synthetic_data(market_prices, volumes)
    current_price = prices[-1]
    sma50 = 105.0  # Price is well above SMA
    # Moderate volatility (2.5% ATR) should give a partial score.
    atr14 = current_price * 0.025
    config = ScorerConfig()

    # Act
    result = score(window_df, market_window_df, current_price, sma50, atr14, config)

    # Assert
    assert "final_score" in result
    assert "relative_strength_score" in result
    assert "description" in result
    assert isinstance(result["final_score"], (float, np.floating))
    assert result["final_score"] > 8.0, "Score should be high in bullish case"
    assert "Volatility" in result["description"]
    assert "RS" in result["description"]


def test_score_flat_scenario() -> None:
    """
    Tests the scorer with a synthetic flat/bearish window.
    - Negative relative strength, no volume surge, price < sma50.
    Expected score should be 0.
    """
    # Arrange: Create a flat window (40 days) with a slight decline
    prices = [100.0] * 30 + [100 - i * 0.2 for i in range(10)]
    volumes = [1000] * 40  # No volume surge
    window_df = _create_synthetic_data(prices, volumes)
    # Market is also flat, so relative strength is negative.
    market_prices = [100.0] * 40
    market_window_df = _create_synthetic_data(market_prices, volumes)
    current_price = prices[-1]
    sma50 = 105.0  # Price is below SMA
    atr14 = current_price * 0.01  # Low volatility, but shouldn't matter
    config = ScorerConfig()

    # Act
    result = score(window_df, market_window_df, current_price, sma50, atr14, config)

    # Assert
    # All positive score components are 0, so total should be 0.
    assert result["final_score"] == 0.0, "Score should be 0 in flat/bearish case"
    assert result["relative_strength_score"] == 0.0
    assert result["sma_score"] == 0.0
    assert result["volume_score"] == 0.0
    assert result["volatility_score"] == 0.0


@pytest.mark.parametrize(
    "stock_return, market_return, expected_rs_score_factor",
    [
        (0.10, 0.05, 1.0),  # Stock up 10%, market up 5% -> 5% outperformance -> max score
        (0.02, 0.07, 0.0),  # Stock up 2%, market up 7% -> underperformance -> zero score
        (0.02, -0.03, 1.0), # Stock up 2%, market down 3% -> 5% outperformance -> max score
        (-0.05, -0.07, 0.4),# Stock down 5%, market down 7% -> 2% outperformance -> partial score
        (0.05, 0.05, 0.0),  # Matched performance -> zero score
    ],
)
def test_relative_strength_score(
    stock_return: float, market_return: float, expected_rs_score_factor: float
):
    """Tests the relative strength score component in isolation."""
    # Arrange
    config = ScorerConfig()
    lookback = config.relative_strength_lookback_days + 1
    # Stock prices that produce the desired return
    stock_prices = [100.0] * (40 - lookback) + list(np.linspace(100.0, 100 * (1 + stock_return), lookback))
    # Market prices that produce the desired return
    market_prices = [100.0] * (40 - lookback) + list(np.linspace(100.0, 100 * (1 + market_return), lookback))

    stock_df = _create_synthetic_data(stock_prices, [1000] * 40)
    market_df = _create_synthetic_data(market_prices, [1000] * 40)

    expected_score = config.relative_strength_score_max * expected_rs_score_factor

    # Act
    result = score(stock_df, market_df, stock_prices[-1], 90.0, 2.0, config)

    # Assert
    assert "relative_strength_score" in result
    assert np.isclose(result["relative_strength_score"], expected_score, atol=1e-2)


def test_score_with_edge_cases() -> None:
    """Tests scorer with edge cases like zero volume or missing SMA."""
    config = ScorerConfig()
    market_window_df = _create_synthetic_data([100.0] * 40, [1000] * 40)

    # Arrange: Zero median volume, should not crash.
    prices = [100.0] * 30 + [101] * 10
    volumes = [0] * 40
    window_df = _create_synthetic_data(prices, volumes)
    result_zero_vol = score(window_df, market_window_df, 101, 99.0, 2.0, config)
    assert result_zero_vol["final_score"] > 3.0  # SMA bonus + RS + volatility

    # Arrange: NaN SMA, should not get SMA bonus
    prices = [100.0 + i for i in range(40)]
    volumes = [1000] * 40
    window_df = _create_synthetic_data(prices, volumes)
    result_nan_sma = score(window_df, market_window_df, prices[-1], np.nan, 2.0, config)
    assert "SMA(0.0)" in result_nan_sma["description"]

    # Arrange: Not enough data for return calc
    prices = [100.0] * 5
    volumes = [1000] * 5
    window_df = _create_synthetic_data(prices, volumes)
    result_short_data = score(window_df, market_window_df, 100.0, 99.0, 2.0, config)
    assert result_short_data["final_score"] == 0.0
    assert "Not enough data" in result_short_data["description"]

    # Arrange: Zero price for division safety
    prices = [10.0] * 30 + [0.0] * 10
    volumes = [1000] * 40
    window_df = _create_synthetic_data(prices, volumes)
    result_zero_price = score(window_df, market_window_df, 0.0, 5.0, 0.1, config)
    assert result_zero_price["final_score"] == 0.0
