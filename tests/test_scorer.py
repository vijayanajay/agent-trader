# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from typing import List

from src.pattern_scorer import score


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
    - Strong 10-day return
    - High recent volume
    - Price above SMA50
    Expected score should be high (close to 10).
    """
    # Arrange: Create a bullish window (40 days)
    prices = [100 + i * 0.5 for i in range(30)] + [115 + i for i in range(10)]
    volumes = [1000] * 35 + [3000] * 5  # Volume surge at the end
    window_df = _create_synthetic_data(prices, volumes)
    current_price = prices[-1]
    sma50 = 105.0  # Price is well above SMA

    # Act
    result = score(window_df, current_price, sma50)

    # Assert
    assert "final_score" in result
    assert "description" in result
    assert isinstance(result["final_score"], (float, np.floating))
    assert result["final_score"] > 8.0, "Score should be high in bullish case"

    # Check description content
    assert "Return" in result["description"]
    assert "Volume" in result["description"]
    assert "SMA(3.0/3)" in result["description"]


def test_score_flat_scenario() -> None:
    """
    Tests the scorer with a synthetic flat/bearish window.
    - Negative 10-day return
    - No volume surge
    - Price below SMA50
    Expected score should be 0.
    """
    # Arrange: Create a flat window (40 days) with a slight decline
    prices = [100.0] * 30 + [100 - i * 0.2 for i in range(10)]
    volumes = [1000] * 40  # No volume surge
    window_df = _create_synthetic_data(prices, volumes)
    current_price = prices[-1]
    sma50 = 105.0  # Price is below SMA

    # Act
    result = score(window_df, current_price, sma50)

    # Assert
    assert "final_score" in result
    assert result["final_score"] == 0.0, "Score should be 0 in flat/bearish case"
    assert "SMA(0.0/3)" in result["description"]


def test_score_with_edge_cases() -> None:
    """Tests scorer with edge cases like zero volume or missing SMA."""
    # Arrange: Zero median volume, should not crash
    prices = [100.0] * 40
    volumes = [0] * 40
    window_df = _create_synthetic_data(prices, volumes)
    result_zero_vol = score(window_df, 100.0, 99.0)
    assert result_zero_vol["final_score"] == 3.0  # Only SMA score

    # Arrange: NaN SMA, should not get SMA bonus
    prices = [100.0 + i for i in range(40)]
    volumes = [1000] * 40
    window_df = _create_synthetic_data(prices, volumes)
    result_nan_sma = score(window_df, prices[-1], np.nan)
    assert "SMA(0.0/3)" in result_nan_sma["description"]

    # Arrange: Not enough data for return calc
    prices = [100.0] * 5
    volumes = [1000] * 5
    window_df = _create_synthetic_data(prices, volumes)
    result_short_data = score(window_df, 100.0, 99.0)
    assert result_short_data["final_score"] == 0.0
    assert "Not enough data" in result_short_data["description"]

    # Arrange: Zero price for division safety
    prices = [10.0] * 30 + [0.0] * 10
    volumes = [1000] * 40
    window_df = _create_synthetic_data(prices, volumes)
    result_zero_price = score(window_df, 0.0, 5.0)
    assert result_zero_price["final_score"] == 0.0
