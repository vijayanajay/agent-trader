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
    - Strong 10-day return, high volume, price > sma50, moderate volatility.
    Expected score should be high.
    """
    # Arrange: Create a bullish window (40 days)
    prices = [100 + i * 0.5 for i in range(30)] + [115 + i for i in range(10)]
    volumes = [1000] * 35 + [3000] * 5  # Volume surge at the end
    window_df = _create_synthetic_data(prices, volumes)
    current_price = prices[-1]
    sma50 = 105.0  # Price is well above SMA
    # Moderate volatility (2.5% ATR) should give a partial score.
    atr14 = current_price * 0.025
    config = ScorerConfig()

    # Act
    result = score(window_df, current_price, sma50, atr14, config)

    # Assert
    assert "final_score" in result
    assert "trend_consistency_score" in result
    assert "description" in result
    assert isinstance(result["final_score"], (float, np.floating))
    # Previous high score was > 8.0. With volatility, it can be higher.
    assert result["final_score"] > 9.0, "Score should be high in bullish case"
    assert "Volatility" in result["description"]
    assert "Trend" in result["description"]


def test_score_flat_scenario() -> None:
    """
    Tests the scorer with a synthetic flat/bearish window.
    - Negative 10-day return, no volume surge, price < sma50.
    Expected score should be 0, regardless of volatility.
    """
    # Arrange: Create a flat window (40 days) with a slight decline
    prices = [100.0] * 30 + [100 - i * 0.2 for i in range(10)]
    volumes = [1000] * 40  # No volume surge
    window_df = _create_synthetic_data(prices, volumes)
    current_price = prices[-1]
    sma50 = 105.0  # Price is below SMA
    atr14 = current_price * 0.01  # Low volatility, but shouldn't matter
    config = ScorerConfig()

    # Act
    result = score(window_df, current_price, sma50, atr14, config)

    # Assert
    # All positive score components are 0, so total should be 0.
    assert result["final_score"] == 0.0, "Score should be 0 in flat/bearish case"
    assert result["return_score"] == 0.0
    assert result["sma_score"] == 0.0
    assert result["volume_score"] == 0.0
    # Volatility score should also be zero'd out by negative return
    assert result["volatility_score"] >= 0.0


@pytest.mark.parametrize(
    "atr_percentage, expected_vol_score_factor",
    [
        (1.0, 1.0),  # Low volatility -> max score
        (5.0, 0.0),  # High volatility -> zero score
        (2.75, 0.5),  # Mid-point -> half score
        (1.5, 1.0),  # Boundary Low
        (4.0, 0.0),  # Boundary High
    ],
)
def test_score_volatility_component(
    atr_percentage: float, expected_vol_score_factor: float
) -> None:
    """Tests the volatility score component in isolation."""
    # Arrange: Create a slightly positive return to enable volatility scoring.
    prices = [100.0] * 30 + [100.1 + i * 0.01 for i in range(10)]
    volumes = [1000] * 40
    window_df = _create_synthetic_data(prices, volumes)
    current_price = prices[-1]
    sma50 = 99.0  # To get SMA bonus, which does not affect volatility score.
    atr14 = current_price * (atr_percentage / 100)
    config = ScorerConfig(
        volatility_target_pct_low=1.5, volatility_target_pct_high=4.0
    )
    expected_score = config.volatility_score_max * expected_vol_score_factor

    # Act
    result = score(window_df, current_price, sma50, atr14, config)

    # Assert
    assert "volatility_score" in result
    assert result["return_score"] > 0, "Return score must be positive to test volatility"
    assert np.isclose(
        result["volatility_score"], expected_score
    ), f"Volatility score for ATR {atr_percentage}% was not as expected."


def test_score_with_edge_cases() -> None:
    """Tests scorer with edge cases like zero volume or missing SMA."""
    config = ScorerConfig()
    # Arrange: Zero median volume, should not crash.
    prices = [100.0] * 30 + [100.1] * 10
    volumes = [0] * 40
    window_df = _create_synthetic_data(prices, volumes)
    result_zero_vol = score(window_df, 100.1, 99.0, 2.0, config)
    assert result_zero_vol["final_score"] > 3.0  # SMA bonus + return + volatility

    # Arrange: NaN SMA, should not get SMA bonus
    prices = [100.0 + i for i in range(40)]
    volumes = [1000] * 40
    window_df = _create_synthetic_data(prices, volumes)
    result_nan_sma = score(window_df, prices[-1], np.nan, 2.0, config)
    assert "SMA(0.0)" in result_nan_sma["description"]

    # Arrange: Not enough data for return calc
    prices = [100.0] * 5
    volumes = [1000] * 5
    window_df = _create_synthetic_data(prices, volumes)
    result_short_data = score(window_df, 100.0, 99.0, 2.0, config)
    assert result_short_data["final_score"] == 0.0
    assert "Not enough data" in result_short_data["description"]

    # Arrange: Zero price for division safety
    prices = [10.0] * 30 + [0.0] * 10
    volumes = [1000] * 40
    window_df = _create_synthetic_data(prices, volumes)
    result_zero_price = score(window_df, 0.0, 5.0, 0.1, config)
    assert result_zero_price["final_score"] == 0.0


def test_score_trend_consistency() -> None:
    """
    Tests that the score correctly penalizes choppy trends and rewards smooth trends,
    even if the total return is similar.
    """
    config = ScorerConfig()
    # --- Case 1: Choppy trend with a big final jump (low consistency) ---
    # 10-day return is 10%, but only 1 up day.
    choppy_prices = [100.0] * 30 + [99.0, 98.0, 97.0, 96.0, 95.0, 94.0, 93.0, 92.0, 91.0, 110.0]
    choppy_window = _create_synthetic_data(choppy_prices, [1000] * 40)
    choppy_result = score(choppy_window, 110.0, 95.0, 2.0, config)

    # Assert consistency is low (1 up day / 10)
    assert choppy_result["trend_consistency_score"] == 0.1
    # Return component should be heavily penalized
    assert choppy_result["return_score"] < 1.0

    # --- Case 2: Smooth, consistent trend (high consistency) ---
    # 10-day return is also 10%, but with 10 up days.
    smooth_prices = [100.0] * 30 + [100.0 + i for i in range(1, 11)] # 101, 102, ... 110
    smooth_window = _create_synthetic_data(smooth_prices, [1000] * 40)
    smooth_result = score(smooth_window, 110.0, 95.0, 2.0, config)

    # Assert consistency is high (10 up days / 10)
    assert smooth_result["trend_consistency_score"] == 1.0
    # Return component should be high
    assert smooth_result["return_score"] > 3.5

    # --- Comparison ---
    # The final score for the smooth trend should be significantly higher.
    assert smooth_result["final_score"] > choppy_result["final_score"]
