import pandas as pd
from typing import Tuple, Optional

__all__ = ["preprocess_data"]

def _calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates the Average True Range (ATR)."""
    high_low = data["High"] - data["Low"]
    high_close = (data["High"] - data["Close"].shift()).abs()
    low_close = (data["Low"] - data["Close"].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    return atr

def preprocess_data(
    full_data: pd.DataFrame, analysis_date: str, window_size: int = 40
) -> Optional[Tuple[pd.DataFrame, float, float]]:
    """
    Prepares the data for a given analysis date.

    Args:
        full_data: DataFrame with historical OHLCV data. Must have a 'Date' index.
        analysis_date: The date for which to prepare the data (e.g., "2023-10-26").
        window_size: The number of trading days to include in the analysis window.

    Returns:
        A tuple containing:
        - A DataFrame with the data for the specified window.
        - The current price (close on analysis_date).
        - The current ATR (on analysis_date).
        Returns None if there is not enough data for the lookback.
    """
    try:
        date_loc = full_data.index.get_loc(analysis_date)
    except KeyError:
        return None

    if date_loc < window_size - 1:
        return None

    start_loc = date_loc - window_size + 1
    window_data = full_data.iloc[start_loc : date_loc + 1].copy()

    # To calculate ATR accurately, we need some data prior to the window
    atr_calc_start_loc = max(0, start_loc - 20)
    atr_calc_data = full_data.iloc[atr_calc_start_loc : date_loc + 1]
    atr = _calculate_atr(atr_calc_data)

    window_data["ATR"] = atr.reindex(window_data.index)

    current_price = window_data.loc[analysis_date, "Close"]
    current_atr = window_data.loc[analysis_date, "ATR"]

    if pd.isna(current_price) or pd.isna(current_atr) or current_atr == 0:
        return None

    return window_data, current_price, current_atr
