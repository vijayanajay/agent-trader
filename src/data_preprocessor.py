# -*- coding: utf-8 -*-
from typing import Optional, Tuple
import numpy as np
import pandas as pd

__all__ = ["preprocess_data"]


def _calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates the Average True Range (ATR) using a simple moving average.
    """
    high_low = data["High"] - data["Low"]
    high_close = (data["High"] - data["Close"].shift()).abs()
    low_close = (data["Low"] - data["Close"].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    # Use simple moving average as per spec (task 2: "simple TR implementation")
    atr = tr.rolling(window=period).mean()
    return atr


def _normalize_window(window_df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes the 'Close' and 'Volume' columns of a DataFrame to a 0-1 scale.
    Handles flat data to prevent division by zero.
    """
    # Normalize 'Close'
    close_min = window_df["Close"].min()
    close_max = window_df["Close"].max()
    if close_max > close_min:
        window_df["close_normalized"] = (
            window_df["Close"] - close_min
        ) / (close_max - close_min)
    else:
        window_df["close_normalized"] = 0.5  # Neutral value if price is flat

    # Normalize 'Volume'
    volume_min = window_df["Volume"].min()
    volume_max = window_df["Volume"].max()
    if volume_max > volume_min:
        window_df["volume_normalized"] = (
            window_df["Volume"] - volume_min
        ) / (volume_max - volume_min)
    else:
        window_df["volume_normalized"] = 0.0  # No volume surge if volume is flat

    return window_df


def preprocess_data(
    full_df: pd.DataFrame, current_date: str, window: int = 40
) -> Optional[Tuple[pd.DataFrame, float, float]]:
    """
    Preprocesses stock data from a DataFrame for a given date.

    Args:
        full_df: DataFrame with the full history for a ticker.
        current_date: The date for analysis (YYYY-MM-DD).
        window: The lookback window size.

    Returns:
        A tuple containing (window_df, current_price, atr14),
        or None if processing is not possible for the given date.
    """
    try:
        target_date = pd.to_datetime(current_date)
        date_loc = full_df.index.get_loc(target_date)
    except KeyError:
        return None  # Date not found, likely a holiday. Skip.

    # Per memory.md, mypy --strict requires asserting the type of get_loc()
    if not isinstance(date_loc, int):
        # This occurs if the index has duplicates and get_loc() returns a slice.
        # For this system, we treat that as an unrecoverable data error.
        return None

    # Ensure there is enough data for a full window AND for ATR calculation lookback
    if date_loc < window:
        return None

    # --- Indicator Calculation ---
    atr14 = _calculate_atr(full_df, period=14)

    # --- Data Slicing ---
    start_loc = date_loc - window + 1
    window_df = full_df.iloc[start_loc : date_loc + 1].copy()

    # --- Normalization ---
    window_df = _normalize_window(window_df)

    current_price_val = full_df.loc[target_date, "Close"]
    current_atr_val = atr14.loc[target_date]

    # Do not proceed if key indicators are not available
    if pd.isna(current_price_val) or pd.isna(current_atr_val):
        return None

    # Explicitly check for numeric types to satisfy mypy --strict
    if not isinstance(current_price_val, (int, float, np.number)) or not isinstance(
        current_atr_val, (int, float, np.number)
    ):
        return None  # Data is not numeric, cannot proceed

    return window_df, float(current_price_val), float(current_atr_val)
